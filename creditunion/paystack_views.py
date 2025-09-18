# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import requests, json
import datetime
from . models import Transaction
from rest_framework import status
from django.contrib.auth import get_user_model
User = get_user_model()






@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_momo_payment(request):
    
    
    """ connect to paystack and initiate momo transaction """
    
    user = request.user
    PAYSTACK_KEY =  settings.PAYSTACK_KEY
    paystack_secret = PAYSTACK_KEY
   
    if not paystack_secret:
        return Response({"error": "Invalid Paystack secret key"}, status=400)

    # initiate a transaction for testing purpose   
    
    headers = {
        "Authorization": f"Bearer {paystack_secret}",
        "Content-Type": "application/json"
    }
    
    data = json.loads(request.body)
    deposit = {
        "email": user.email,
        'amount': data.get('amount'),
        'network': data.get('network'),
        'phone_number': data.get('phone_number'),
        'date': datetime.date.today(),
        "callback_url": settings.PAYSTACK_CALLBACK_URL
    }
    
    # print(deposit)
    
    payload = {
        "email": user.email,
        "amount": round(float(deposit["amount"])),  # Paystack uses Kobo
        # "callback_url": settings.PAYSTACK_CALLBACK_URL
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=payload)

    if response.status_code == 200 and response.json().get("status"):
        data = response.json()["data"]
        

        return Response({
            "status": "success",
            "authorization_url": data["authorization_url"],
            "reference": data["reference"],
           
                'payment_data': {
                    'transaction_type':'deposit',
                    'email':deposit['email'],
                    'amount': deposit['amount'],
                    'network':deposit['network'],
                    'phone_number': deposit['phone_number'],
                    'notes':'momo deposit',
                    'member': user.id
                    
                }
             
        })
        
    return Response({
        "error": "Failed to initiate payment",
        "details": response.json()
    }, status=400)

    


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_transaction(request):
    """
    Verifies Paystack transaction and records deposit if successful
    Endpoint: /api/verify-transaction/?reference=<ref>
    """
    user = request.user
    reference = request.GET.get("reference")

    if not reference:
        return Response({"error": "Transaction reference is required."}, status=400)

    verification = verify_paystack_transaction(reference)

    if verification["status"] == "success":
        data = verification["data"]
        
        # print(data)

        if data["status"] == "success":
            # ✅ Transaction was successful, now record in DB
            Transaction.objects.create(
                amount=data["amount"] ,  # Convert from kobo to Naira
                member=user,
                transaction_type="deposit",
                date=datetime.date.today(),
                notes="momo deposit",
            )

            return Response({
                "status": "success",
                "message": "Transaction verified and recorded successfully.",
                "amount": data["amount"] ,
                "reference": reference
            })

        else:
            return Response({
                "status": "pending",
                "message": f"Transaction is not completed: {data['status']}"
            })

    else:
        return Response({
            "status": "failed",
            "message": verification["message"]
        }, status=400)









def verify_paystack_transaction(reference):
    """Call Paystack API to verify a transaction by reference"""
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200 and data["status"]:
            return {
                "status": "success",
                "data": data["data"]
            }
        else:
            return {
                "status": "failed",
                "message": data.get("message", "Verification failed"),
                "data": data
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }
