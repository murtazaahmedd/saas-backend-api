"""Permission names (resource.action). Use the attributes at call sites so a rename propagates."""


class ProjectPermissions:
    read = "project.read"
    create = "project.create"
    update = "project.update"
    delete = "project.delete"


class UserPermissions:
    read = "user.read"
    create = "user.create"


project = ProjectPermissions()
user = UserPermissions()
