from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .auth_token import CustomAuthToken


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import auth_views, dashboard_views, loanSummary_view, model_viewset, paystack_views

from .loan_viewset import LoanViewSet, LoanRepaymentViewSet


router = DefaultRouter()
router.register(r'transactions', model_viewset.TransactionViewSet, basename='transaction')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'loan-repayments', LoanRepaymentViewSet, basename='loan-repayment')



urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),
    
    path('api/auth-signup/', auth_views.signup, name='auth-signup'),
    path('api/auth-signin/', auth_views.signin, name='auth-signin'),
    path('api/auth-signout/', auth_views.signout, name='auth-signout'),
    
    
     path("api/member/change-password/", auth_views.change_password, name="change-password"),
    
    
    # paystack api
    #path('api/connect-paystack/', paystack_views.connect_paystack, name='connect-paystack'),
    path('api/connect-paystack/', paystack_views.initiate_momo_payment, name='initiate-momo-payment'),
    # path('api/verify-transaction/<str:reference>/', paystack_views.verify_transaction, name='verify-transaction'),
    
    path("api/verify-transaction/", paystack_views.verify_transaction, name='verify-transaction'),
    
    path('api/all-members/', model_viewset.AllMembersAPIView.as_view(), name='all-members'),
    
    #dashboard views
    path('api/member-dashboard/', dashboard_views.MemberDashboardView.as_view(), name='member-dashboard'),
    
    path('api/user-transactions/', model_viewset.UserTransactionListView.as_view(), name='user-transactions'),
    
    #loan summary
    path('api/loan-summary/', loanSummary_view.loan_summary, name='loan-summary'),
    
    #only loan history endpoint
    path('api/loan-history/', loanSummary_view.loan_history_view, name='loan-history'),
    
    
    # all loan applications
    path('api/loan-list/', loanSummary_view.loan_list, name='loan-list'),
    
    
    path('api/member/profile/', model_viewset.MemberProfileView.as_view(), name='member-profile'),
    
    
    path('api/churches/', model_viewset.church_list, name='church-list'),
]