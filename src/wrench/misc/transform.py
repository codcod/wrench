import typing as tp

JQ_FLATTEN = """
.[] | [
    {
        name:               .metadata.name,
        title:              .metadata.title,
        description:        .metadata.description,
        owner:              .spec.owner,
        docs:               .metadata.annotations."backbase/docs-link",
        type:               .spec.type,
        lifecycle:          .spec.lifecycle,
        "subcomponent-of":  .spec.subcomponentOf,
        kind:               .kind,
        catalog:            .metadata.annotations."backstage.io/view-url",
        "maint-component":  .metadata.annotations."jira/maint-component",
        "maint-subcomponent": .metadata.annotations."jira/maint-subcomponent",
        "jira-key":         .metadata.annotations."jira/project-key",
        "jira-component":   .metadata.annotations."jira/project-component",
        slack:              .metadata.annotations."slack/conversation-id",
        slack:              .metadata.annotations."slack/conversation-id",
    }
] | map
(
    with_entries(select(.key != .metadata))
    +
    .metadata |del(.metadata)
) | .[]"""


def transform(data: tp.Any, jq_function: str) -> tp.Any:
    import jq

    program = jq.compile(jq_function)
    print(data)
    filtered = program.input_value(data).all()
    return filtered
