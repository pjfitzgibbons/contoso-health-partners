<?php
/**
 * Plugin Name: Contoso publishing role
 * Description: Registers the least-privilege WordPress role used by the wp-publish toolchain, and nothing else.
 * Version:     1
 * Author:      Peter Fitzgibbons
 *
 * Install as a must-use plugin:
 *
 *     wp-content/mu-plugins/wp-publisher-role.php
 *
 * mu-plugins load unconditionally and cannot be deactivated from WP Admin, which
 * is what we want: the capability set of a credential an agent drives should not
 * be one checkbox away from changing. This file is the reviewable record of that
 * set -- a role edited through a plugin UI leaves no diff and no history.
 *
 * WHY A CUSTOM ROLE AND NOT 'author'
 *
 * The toolchain needs one capability no built-in role has (view_koko_analytics,
 * which Koko Analytics grants to administrator alone), and Author carries three
 * it has no use for (upload_files, delete_posts, delete_published_posts). There
 * is no built-in role that is a superset of what is needed and a subset of what
 * is safe, so the role is enumerated here instead.
 *
 * Capabilities are a deny-by-default list: anything absent below is denied.
 */

declare(strict_types=1);

namespace Contoso\Publisher;

defined('ABSPATH') || exit;

const ROLE = 'wp_publisher';

/**
 * Bump this when CAPS changes. The role is only rewritten when the stored
 * version differs, so this file costs one option read per request and no
 * writes once it has settled.
 */
const VERSION = 2;

const CAPS = [
    // Read the REST API at all, and answer --whoami.
    'read'                  => true,

    // Create and edit posts. This also carries assign_terms for categories and
    // tags, since both taxonomies map assign_terms to edit_posts -- so existing
    // terms can be attached to a post without any capability over the taxonomy
    // itself. Measured 2026-10-10: it ALSO permits creating a tag, while
    // editing or deleting any term is still refused. See manage_categories.
    'edit_posts'            => true,

    // Honour `status: publish` in a post's frontmatter.
    'publish_posts'         => true,

    // Re-running the script on a file whose post is already live is an update,
    // not a new post, and updating a published post needs this.
    'edit_published_posts'  => true,

    // Edit a post belonging to another user. Granted reluctantly, and only
    // because WordPress uses one field -- post_author -- as BOTH the
    // access-control subject and the public byline. Every post already on the
    // site is authored by Peter (user 2), so without this the toolchain could
    // create new posts and never update an existing one. Measured 2026-10-10
    // with VERSION 1: a no-op update of W1 returned 403 "not allowed to edit
    // this post", and an edit-context post listing returned 0 rows.
    //
    // The alternative was to reassign posts to this account, which changes the
    // byline the site displays. On a project whose subject is authorship as a
    // control, a service account must not become the author of record. So the
    // byline stays correct and the capability is widened instead. The added
    // reach is bounded: this blog has one human author, and the account still
    // cannot delete, upload, moderate, or alter a taxonomy.
    'edit_others_posts'     => true,

    // Read traffic: Koko Analytics gates /wp-json/koko-analytics/v1/* on this.
    // It is read-only; managing Koko's settings is manage_koko_analytics, which
    // is deliberately NOT granted.
    'view_koko_analytics'   => true,

    // --- Deliberately withheld, with the reason, so a future reader does not
    // --- "fix" an omission that is the point. Every line below was tested
    // --- against the live site on 2026-10-10, not inferred from the docs.
    //
    // manage_categories    Renames and DELETES every category and tag on the
    //                      site. Withheld -- and it turns out nothing is lost:
    //                      the account can create a tag without it, yet cannot
    //                      edit or delete any term, not even one it just
    //                      created. Create-without-destroy is exactly the split
    //                      we want, and it is the platform's, not ours.
    // unfiltered_html      Lets post content carry <script>. A credential an
    //                      agent drives must not be able to put executable
    //                      JavaScript on the site. Measured: KSES leaves every
    //                      shape the toolchain emits intact -- block
    //                      delimiters, block attribute JSON, the generated
    //                      wp-block-syntaxhighlighter-code class, wp:list-item
    //                      wrappers, the wp:html footnotes div, and data-
    //                      attributes -- while stripping <script>. Withholding
    //                      it costs nothing.
    // upload_files         The toolchain sends no media.
    // delete_posts         Publishing is not deleting. Removing a post is a
    // delete_published_posts   human decision taken in WP Admin. Verified: the
    //                      account cannot delete even a draft it just created.
    // moderate_comments    Approving, spamming and deleting comments all ride
    //                      on this one capability, so it cannot be granted for
    //                      reading alone. The consequence is that wp_report.py
    //                      sees approved comments only and prints '?' for the
    //                      held, spam and trash counts rather than a wrong 0.
    // activate_plugins     wp_report.py's traffic probe reads the plugin list
    //                      when it can. Without this it degrades to the REST
    //                      namespace check and the page scan, which is enough:
    //                      Koko registers koko-analytics/v1.
    // manage_options       Site settings. Refused, verified.
    // list_users, edit_users, install_plugins, and the rest of administrator:
    //                      never needed to publish a blog post.
];

add_action('init', static function (): void {
    if ((int) get_option('contoso_publisher_role_version', 0) === VERSION) {
        return;
    }

    // Removed and re-added rather than patched, so that a capability deleted
    // from CAPS is actually revoked. Users keep the role by name, so they pick
    // up the new set on the next request.
    remove_role(ROLE);
    add_role(ROLE, 'Publishing toolchain', CAPS);

    update_option('contoso_publisher_role_version', VERSION, true);
}, 5);
