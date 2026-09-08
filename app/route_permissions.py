TENANT_ADMIN_ROUTES = [
    '/tenants',
    '/edit-tenant-attribute',
    '/delete-tenant-attribute/*',
    '/tenant/*',
    '/tenant-set-is-disable',
    '/user-profile',
    '/edit-user-attribute',
    '/delete-user-attribute/*',
    '/get-tenants',
    '/add-user-attribute/<username>',
    '/reset-password-attributes/<username>',
    '/tenant-set-is-sftp/*'
]


BASIC_USER_ROUTES = [
    '/user-profile',
    '/edit-user-attribute',
    '/delete-user-attribute/*',
    '/add-user-attribute/<username>',
    '/reset-password-attributes/<username>',
]