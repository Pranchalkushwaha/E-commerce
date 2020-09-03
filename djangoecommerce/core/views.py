from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from .models import Order, Item, OrderItem, BillingAddress, Payment, Coupon
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import CheckoutForm

import stripe
stripe.api_key = 'sk_test_OrQwuL57Skdcm6SvowLXjxmj'



# Create your views here.
def products(request): 
    context = {
        'items' : Items.objects.all()
    }
    return render(request, 'home-page.html')

class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form' : form
        }
        return render(self.request, 'checkout-page.html', context)
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address') 
                country = form.cleaned_data.get('country') 
                zip = form.cleaned_data.get('zip') 
                # same_shipping_address = form.cleaned_data.get('same_shipping_address') 
                # save_info = form.cleaned_data.get('save_info') 
                payment_options = form.cleaned_data.get('payment_options')  
                billing_address = BillingAddress(
                    user = self.request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    country = country,
                    zip = zip,
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_options == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_options == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, 'Invalid Payment option')
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return redirect('/')

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self .request.user, ordered=False)
        context = {
            'order' : order
        }
        return render(self.request, 'payment.html')
    
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self .request.user, ordered=False)
        token = self.request.POST.get('stripeToken ')
        amount = int(order.get_total() * 100)
        try:

            # if use_default or save:
            #     charge the customer because we cannot charge the token more than once
            # charge = stripe.Charge.create(
            #     amount=amount,  # cents
            #     currency="usd",
            #     customer=userprofile.stripe_customer_id
            # )
            # else:
            #     charge once off on the token
            charge = stripe.Charge.create(
                amount=amount,  # cents
                currency="usd",
                source=token
            )

            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to the order

            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()
            


            order.ordered = True
            order.payment = payment
            # order.ref_code = create_ref_code()
            order.save()

            messages.success(self.request, "Your order was successful!")
            return redirect("/")

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            print(e)
            messages.warning(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request, "Something went wrong. You were not charged. Please try again.")
            return redirect("/")

        except Exception as e:
            # send an email to ourselves
            messages.warning(
                self.request, "A serious error occurred. We have been notifed.")
            return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")






def home(request):
    context = {
        'items' : Item.objects.all()
    }
    return render(request, 'home-page.html', context)



class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = 'home-page.html'


class OrderSummaryView(LoginRequiredMixin ,View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object' : order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(request, 'You do not have an active order')
            return redirect('/')
        


class ProductDetailView(DetailView):
    model = Item
    template_name = "product-page.html"

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'This item is updated to your cart')
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, 'This item is added to your cart')
            return redirect("core:order-summary")
    else:
        start_date = timezone.now()
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, start_date=start_date, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, 'This item is added to your cart')
    return redirect("core:order-summary")

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, 
                user=request.user, 
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, 'This item is removed from your cart')
            return redirect("core:order-summary")
        else:
            messages.info(request, 'This item is not in your cart')
            return redirect("core:product", slug=slug)
    else:
        # add a message saying the user doesnt have an order
        messages.info(request, 'You do not have an active your cart')
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, 
                user=request.user, 
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, 'This item quantity is updated')
            return redirect("core:order-summary")
        else:
            messages.info(request, 'This item is not in your cart')
            return redirect("core:product")
    else:
        # add a message saying the user doesnt have an order
        messages.info(request, 'You do not have an active your cart')
        return redirect("core:product")
    return redirect("core:product")



def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")