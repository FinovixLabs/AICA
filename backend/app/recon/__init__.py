"""GSTR-2B Reconciliation and IMS Portal.

Self-contained namespace. Nothing in the pre-existing codebase imports this tree.
The only symbols this package takes from the rest of the app are the three
tenancy functions every existing router already depends on:

    app.core.db.get_db
    app.api.deps.get_or_create_default_ca
    app.api.deps.require_client

Where reuse would mean depending on another module's *private* helper, this
package keeps its own copy instead. See app/recon/core/normalize.py for the
worked example. Full uninstall: backend/migrations/manual/999_drop_recon.sql plus
deleting this tree.
"""
