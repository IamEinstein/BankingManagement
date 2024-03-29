from django.db import models
import uuid
import bcrypt
from django.shortcuts import render, redirect
import json

categories = (
    ("Groceries", "Groceries"),
    ("Transportation", "Transportation"),
    ("Dining", "Dining"),
    ("Entertainment", "Entertainment"),
    ("Clothing", "Clothing"),
    ("Debt Payments", "Debt Payments"),
    ("Healthcare", "Healthcare"),
    ("Insurance", "Insurance"),
    ("Investment", "Investment"),
    ("Taxes", "Taxes"),
    ("Education", "Education"),
    ("Charitable Donations", "Charitable Donations"),
    ("Travel", "Travel"),
    ("Business Expenses", "Business Expenses"),
    ("Rent", "Rent"),
    ("Utilities", "Utilities"),
    ("Loan Payments", "Loan Payments"),
    #   ("Money Earned", "Money Earned"),
)

currencies = (("USD", "United States Dollar"), ("EUR", "Euro"),
              ("JPY", "Japanese Yen"), ("GBP", "British Pound Sterling"),
              ("AUD", "Australian Dollar"), ("CAD", "Canadian Dollar"),
              ("CHF", "Swiss Franc"), ("CNY", "Chinese Yuan"),
              ("INR", "Indian Rupee"), ("BRL", "Brazilian Real"),
              ("RUB", "Russian Ruble"), ("KRW", "South Korean Won"),
              ("MXN", "Mexican Peso"), ("ZAR", "South African Rand"),
              ("SGD", "Singapore Dollar"), ("NZD", "New Zealand Dollar"),
              ("HKD", "Hong Kong Dollar"), ("SEK", "Swedish Krona"),
              ("NOK", "Norwegian Krone"), ("TRY", "Turkish Lira"))


class User(models.Model):
    username = models.CharField(max_length=25, unique=True)
    password = models.BinaryField(editable=True)
    name = models.CharField(max_length=200, null=True)
    bank_balance = models.BigIntegerField(default=100)
    unique_id = models.UUIDField(unique=True,
                                 default=uuid.uuid4,
                                 editable=False)
    transaction_list = models.CharField(max_length=10485700,
                                        null=True,
                                        default=None)
    currency = models.CharField(max_length=256,
                                choices=currencies,
                                default="USD")
    friends_list = models.CharField(max_length=10485700,
                                    null=True,
                                    default=None)
    no_of_friends = models.IntegerField(default=0)

    def __str__(self):
        return self.username

    def authenticate(self, pwd, request, bot=False):
        if bot is False:
            if type(self.password) == memoryview:
                if bcrypt.checkpw(bytes(pwd, 'utf-8'),
                                  self.password.tobytes()):
                    response = render(request,
                                      'main/logout.html',
                                      context={
                                          "title": "Login",
                                          "text": "Logging you in"
                                      })
                    response.set_cookie("user-identity",
                                        str(self.unique_id),
                                        max_age=31556952)
                    return response
                return render(request,
                              "main/login.html",
                              context={"error": "Password is incorrect"})
            else:
                if bcrypt.checkpw(bytes(pwd, 'utf-8'), self.password):
                    response = render(request,
                                      'main/logout.html',
                                      context={
                                          "title": "Login",
                                          "text": "Logging you in"
                                      })
                    response.set_cookie("user-identity", str(self.unique_id))
                    return response
                return render(request,
                              "main/login.html",
                              context={"error": "Password is incorrect"})

        elif bot == True:
            return render(request,
                          "main/login.html",
                          context={"error": "Password is incorrect"})

    def transaction(self, new_transaction_created):
        jsonDec = json.decoder.JSONDecoder()
        try:
            current_list = jsonDec.decode(self.transaction_list)
        except (TypeError, json.decoder.JSONDecodeError):
            current_list = []

        current_list.append(str(new_transaction_created.transaction_id))
        self.transaction_list = json.dumps(current_list)
        self.save()
        new_transaction_created.save()
        return True

    @staticmethod
    def get_user(request=None):
        try:
            request.COOKIES['user-identity']
        except (KeyError, AttributeError):
            return redirect("main:login")
        else:
            id = request.COOKIES['user-identity']
            try:
                user = User.objects.get(unique_id=id)
            except User.DoesNotExist:
                res = render(request,
                             "main/logout.html",
                             context={"text": "Loading"})
                res.delete_cookie("user-identity")
                return res
            else:
                return user

    @staticmethod
    def logout(request=None):
        try:
            request.COOKIES['user-identity']
        except KeyError:
            return redirect("main:index")
        else:
            response = render(request,
                              'main/logout.html',
                              context={
                                  "title": "Logout",
                                  "text": "Logging you out"
                              })
            response.delete_cookie("user-identity")
            return response

    def get_transactions(self):
        jsonDec = json.decoder.JSONDecoder()
        transaction_list = []
        try:
            for id in jsonDec.decode(self.transaction_list):
                to_append = Transaction.objects.get(transaction_id=id)
                transaction_list.append(to_append)
            return transaction_list
        except Transaction.DoesNotExist:
            return None

    def get_friends(self):
        jsonDec = json.decoder.JSONDecoder()
        friends_list = []
        try:
            for id in jsonDec.decode(self.friends_list):
                frnd = User.objects.get(unique_id=id)
                friends_list.append(frnd)
            return friends_list
        except (User.DoesNotExist, TypeError, json.decoder.JSONDecodeError):
            return None

    def add_friend(self, username):
        jsonDec = json.decoder.JSONDecoder()
        friends_list = []
        try:
            for id in jsonDec.decode(self.friends_list):
                friends_list.append(id)
        except (User.DoesNotExist, TypeError):
            friends_list = []
        try:
            friend = User.objects.get(username=username)
        except User.DoesNotExist:
            return False
        else:
            if friend.unique_id == self.unique_id:
                return False
            friends_list.append(str(friend.unique_id))
            self.friends_list = json.dumps(list(set(friends_list)))
            self.save()
            return True

    # def remove_friend(self, username):
    #     jsonDec = json.decoder.JSONDecoder()
    #     friends_list = []
    #     try:
    #         for id in jsonDec.decode(self.friends_list):
    #             friends_list.append(id)
    #     except (User.DoesNotExist, TypeError):
    #         friends_list = []
    #     try:
    #         friend = User.objects.get(username=username)
    #     except User.DoesNotExist:
    #         friends_list.remove(username)
    #     else:


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.BigIntegerField(null=False, default=100)
    type = models.CharField(max_length=10,
                            choices=(("Add", "Add"), ("Withdraw", "Withdraw")))
    reason = models.CharField(max_length=256,
                              default="No Reason provided",
                              null=False)
    transaction_id = models.UUIDField(unique=True,
                                      default=uuid.uuid4,
                                      editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=256,
                                default="Money Earned",
                                choices=categories)

    def __str__(self):
        return f"{self.user.name} - {self.type} -> {self.amount}"
