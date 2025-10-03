@login_required
def user_financial_info_api(request):
    """API endpoint that returns user's financial information."""
    try:
        user = request.user
        return "test"
    except Exception as e:
        return "error"