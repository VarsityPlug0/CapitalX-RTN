"""
Admin Roles Configuration for CapitalX Platform
================================================

Defines role-based access control (RBAC) for the unified admin dashboard.
Each role has a set of permissions that control which sections are visible and accessible.
"""

# Admin role definitions with their permissions
ADMIN_ROLES = {
    'super_admin': {
        'name': 'Super Admin',
        'description': 'Full access to all admin features',
        'permissions': ['all'],
        'icon': 'fas fa-crown',
    },
    'finance_admin': {
        'name': 'Finance Admin',
        'description': 'Manage deposits, withdrawals, and investments',
        'permissions': ['dashboard', 'deposits', 'withdrawals', 'investments'],
        'icon': 'fas fa-money-bill-wave',
    },
    'user_admin': {
        'name': 'User Admin',
        'description': 'Manage users and referrals',
        'permissions': ['dashboard', 'users', 'referrals'],
        'icon': 'fas fa-users-cog',
    },
    'marketing_admin': {
        'name': 'Marketing Admin',
        'description': 'Manage leads and campaigns',
        'permissions': ['dashboard', 'leads', 'campaigns'],
        'icon': 'fas fa-bullhorn',
    },
    'content_admin': {
        'name': 'Content Admin',
        'description': 'Manage companies and investment plans',
        'permissions': ['dashboard', 'companies', 'investment_plans'],
        'icon': 'fas fa-edit',
    },
}

# Role choices for the CustomUser model
ADMIN_ROLE_CHOICES = [
    ('', 'No Admin Role'),
    ('super_admin', 'Super Admin'),
    ('finance_admin', 'Finance Admin'),
    ('user_admin', 'User Admin'),
    ('marketing_admin', 'Marketing Admin'),
    ('content_admin', 'Content Admin'),
]

# Navigation sections for the admin sidebar
ADMIN_NAV_SECTIONS = [
    {
        'id': 'dashboard',
        'name': 'Dashboard',
        'icon': 'fas fa-tachometer-alt',
        'url_name': 'admin_dashboard',
        'permissions': ['dashboard'],  # All roles have dashboard access
    },
    {
        'id': 'financial',
        'name': 'Financial Management',
        'icon': 'fas fa-money-bill-wave',
        'permissions': ['deposits', 'withdrawals', 'investments'],
        'children': [
            {
                'id': 'deposits',
                'name': 'Deposits',
                'icon': 'fas fa-file-invoice-dollar',
                'url_name': 'admin_deposits',
                'permissions': ['deposits'],
            },
            {
                'id': 'withdrawals',
                'name': 'Withdrawals',
                'icon': 'fas fa-money-check-alt',
                'url_name': 'admin_withdrawals',
                'permissions': ['withdrawals'],
            },
            {
                'id': 'investments',
                'name': 'Investments',
                'icon': 'fas fa-chart-line',
                'url_name': 'admin_investments',
                'permissions': ['investments'],
            },
        ],
    },
    {
        'id': 'users_section',
        'name': 'User Management',
        'icon': 'fas fa-users',
        'permissions': ['users', 'referrals'],
        'children': [
            {
                'id': 'users',
                'name': 'Users',
                'icon': 'fas fa-user',
                'url_name': 'admin_users',
                'permissions': ['users'],
            },
            {
                'id': 'referrals',
                'name': 'Referrals',
                'icon': 'fas fa-user-friends',
                'url_name': 'admin_referrals',
                'permissions': ['referrals'],
            },
        ],
    },
    {
        'id': 'content_section',
        'name': 'Content',
        'icon': 'fas fa-building',
        'permissions': ['companies', 'investment_plans'],
        'children': [
            {
                'id': 'companies',
                'name': 'Companies',
                'icon': 'fas fa-building',
                'url_name': 'admin_companies',
                'permissions': ['companies'],
            },
            {
                'id': 'investment_plans',
                'name': 'Investment Plans',
                'icon': 'fas fa-chart-bar',
                'url_name': 'admin_investment_plans',
                'permissions': ['investment_plans'],
            },
        ],
    },
    {
        'id': 'marketing_section',
        'name': 'Marketing',
        'icon': 'fas fa-bullhorn',
        'permissions': ['leads', 'campaigns'],
        'children': [
            {
                'id': 'leads',
                'name': 'Lead Dashboard',
                'icon': 'fas fa-envelope',
                'url_name': 'admin_leads',
                'permissions': ['leads'],
            },
            {
                'id': 'campaigns',
                'name': 'Campaigns',
                'icon': 'fas fa-paper-plane',
                'url_name': 'admin_campaigns',
                'permissions': ['campaigns'],
            },
        ],
    },
    {
        'id': 'system',
        'name': 'System',
        'icon': 'fas fa-cogs',
        'permissions': ['all'],  # Only super admins
        'children': [
            {
                'id': 'database_admin',
                'name': 'Database Admin',
                'icon': 'fas fa-database',
                'url': '/capitalx_admin/',  # External URL
                'permissions': ['all'],
            },
        ],
    },
]


def get_user_permissions(user):
    """
    Get the list of permissions for a user based on their role.
    
    Args:
        user: CustomUser instance
        
    Returns:
        list: List of permission strings the user has
    """
    if not user.is_authenticated:
        return []
    
    # Superusers have all permissions
    if user.is_superuser:
        return ['all']
    
    # Staff without specific role get basic permissions
    if not user.is_staff:
        return []
    
    # Get role-based permissions
    admin_role = getattr(user, 'admin_role', None)
    if admin_role and admin_role in ADMIN_ROLES:
        return ADMIN_ROLES[admin_role]['permissions']
    
    # Default staff permissions (dashboard only)
    return ['dashboard']


def has_permission(user, required_permissions):
    """
    Check if a user has any of the required permissions.
    
    Args:
        user: CustomUser instance
        required_permissions: list of permission strings
        
    Returns:
        bool: True if user has at least one required permission
    """
    user_perms = get_user_permissions(user)
    
    # 'all' permission grants access to everything
    if 'all' in user_perms:
        return True
    
    return any(perm in user_perms for perm in required_permissions)


def get_visible_nav_sections(user):
    """
    Get navigation sections visible to the user based on their permissions.
    
    Args:
        user: CustomUser instance
        
    Returns:
        list: List of navigation section dicts the user can see
    """
    user_perms = get_user_permissions(user)
    visible_sections = []
    
    for section in ADMIN_NAV_SECTIONS:
        # Check if user has permission for this section
        section_perms = section.get('permissions', [])
        
        if 'all' in user_perms or any(p in user_perms for p in section_perms):
            # Deep copy the section to avoid modifying original
            visible_section = {
                'id': section['id'],
                'name': section['name'],
                'icon': section['icon'],
            }
            
            # Add URL if present
            if 'url_name' in section:
                visible_section['url_name'] = section['url_name']
            if 'url' in section:
                visible_section['url'] = section['url']
            
            # Filter children by permissions
            if 'children' in section:
                visible_children = []
                for child in section['children']:
                    child_perms = child.get('permissions', [])
                    if 'all' in user_perms or any(p in user_perms for p in child_perms):
                        visible_children.append(child)
                
                if visible_children:
                    visible_section['children'] = visible_children
                else:
                    continue  # Skip section if no visible children
            
            visible_sections.append(visible_section)
    
    return visible_sections
