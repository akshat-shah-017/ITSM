// Auth - Role constants and helpers
// Role IDs are server-defined - DO NOT HARD-CODE STRINGS

/**
 * Role IDs as defined by the backend.
 * These are stable and will not change.
 */
export const Roles = {
    USER: 1,
    EMPLOYEE: 2,
    MANAGER: 3,
    ADMIN: 4,
} as const;

export type RoleId = (typeof Roles)[keyof typeof Roles];

/**
 * Map role IDs to role names (as returned by backend)
 */
export const RoleIdToName: Record<number, string> = {
    [Roles.USER]: 'USER',
    [Roles.EMPLOYEE]: 'EMPLOYEE',
    [Roles.MANAGER]: 'MANAGER',
    [Roles.ADMIN]: 'ADMIN',
};

/**
 * Map role names to role IDs
 */
export const RoleNameToId: Record<string, number> = {
    USER: Roles.USER,
    EMPLOYEE: Roles.EMPLOYEE,
    MANAGER: Roles.MANAGER,
    ADMIN: Roles.ADMIN,
};

/**
 * Check if user roles (from API) include a specific role ID
 */
export function hasRole(userRoles: string[], roleId: number): boolean {
    const roleName = RoleIdToName[roleId];
    if (!roleName) return false;
    return userRoles.includes(roleName);
}

/**
 * Check if user roles include any of the specified role IDs
 */
export function hasAnyRole(userRoles: string[], roleIds: number[]): boolean {
    return roleIds.some((roleId) => hasRole(userRoles, roleId));
}

/**
 * Check if user has at least the specified role level
 * Higher role IDs have more permissions (USER=1 < EMPLOYEE=2 < MANAGER=3 < ADMIN=4)
 */
export function hasMinRole(userRoles: string[], minRoleId: number): boolean {
    const userRoleIds = userRoles
        .map((name) => RoleNameToId[name])
        .filter((id): id is number => id !== undefined);

    return userRoleIds.some((id) => id >= minRoleId);
}

/**
 * Get the highest role ID from user roles
 */
export function getMaxRoleId(userRoles: string[]): number {
    const userRoleIds = userRoles
        .map((name) => RoleNameToId[name])
        .filter((id): id is number => id !== undefined);

    if (userRoleIds.length === 0) return 0;
    return Math.max(...userRoleIds);
}

/**
 * Check if user is at least an employee (can access employee routes)
 */
export function isAtLeastEmployee(userRoles: string[]): boolean {
    return hasMinRole(userRoles, Roles.EMPLOYEE);
}

/**
 * Check if user is at least a manager (can access manager routes)
 */
export function isAtLeastManager(userRoles: string[]): boolean {
    return hasMinRole(userRoles, Roles.MANAGER);
}

/**
 * Check if user is an admin
 */
export function isAdmin(userRoles: string[]): boolean {
    return hasRole(userRoles, Roles.ADMIN);
}
