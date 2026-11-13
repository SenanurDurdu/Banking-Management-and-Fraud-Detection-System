from auth import AuthMixin
from customers import CustomersMixin
from accounts import AccountsMixin
from transactions import TransactionsMixin
from fraud import FraudMixin
from dashboard import DashboardMixin


class Bank(
    AuthMixin,
    CustomersMixin,
    AccountsMixin,
    TransactionsMixin,
    FraudMixin,
    DashboardMixin
):
    pass