"""Select only the independently commissioned Docs component implementation."""

import importlib

import oracle_owner as owner


def for_binding(binding):
    owner.require(
        owner.is_docs_binding(binding),
        "EXACT_INDEPENDENT_DOCS_DRIVER_SCOPE_REQUIRED",
    )
    if binding["repository"] == owner.CONSOLIDATED_REPOSITORY:
        owner.docs_operational_source(binding)
    return importlib.import_module(
        "oracle_docs_runner"
        if binding["component"] == "docs-public"
        else "oracle_docs_internal_runner"
    )


def for_component(store, component=None):
    canonical = owner.CONSOLIDATED_REPOSITORY + ":platform:docs-public"
    if canonical in store.policy["components"]:
        owner.require(
            set(store.policy["components"]) == {canonical}
            and component in {None, "docs-public"},
            "ONE_CANONICAL_PUBLIC_DOCS_COMPONENT_REQUIRED",
        )
        return for_binding(
            {**store.policy["toolchain"]["source_binding"], "component": "docs-public"}
        )
    if component is None:
        components = set(store.policy["components"])
        owner.require(
            len(components) == 1,
            "ONE_INDEPENDENT_DOCS_COMPONENT_PER_INSTALLATION_REQUIRED",
        )
        repository, component = next(iter(components)).split(":")
    else:
        repository = "DruHustle/onesa-ai-platform"
    binding = {"repository": repository, "component": component}
    owner.require(
        repository + ":" + component in store.policy["components"],
        "COMMISSIONED_DOCS_COMPONENT_REQUIRED",
    )
    return for_binding(binding)
