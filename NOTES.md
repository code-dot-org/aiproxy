Here's the issue, we don't grant enough permissions for our application stack to include iam permissions, but it's totally appropriate for that stack to define roles and policies for it's own resources. We do need some protection, and don't want people defining policies in the ap template that allow permission escalation elsewhere, but this is all tracked by git and requires PR's, so I think it's an accpetable risk and we can tighten it up later.

Strategy:

eliminate imports from app template and define things as close to their use as possible

see what breaks

create new global iam roles as needed

GOAL:
- admin still required for setup
- anybody can deploy cicd