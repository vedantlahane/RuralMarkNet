# RuralMarkNet

RuralMarkNet is a Django-based marketplace that connects farmers with local customers. Farmers publish produce listings, manage delivery schedules, and track payments. Customers browse, order, and schedule doorstep delivery in their preferred language.

## Features

- Product catalogue with rich filtering (category, price range, availability, farmer)
- Role-aware onboarding for farmers and customers using a custom user model
- Session-backed cart, checkout flow, delivery scheduling, and order tracking
- Payment abstraction layer with Stripe and PayPal placeholders and webhook entrypoints
- Delivery management dashboard for farmers and customers
- Internationalisation enabled for English and Hindi with a language selector
- Tailwind CSS integration via `django-tailwind` for responsive UI theming
- Django admin configured for all core entities

## Project Structure

```
accounts/      # Custom user model, authentication views, dashboards
products/      # Product catalogue logic, filtering, farmer management
orders/        # Cart, checkout, order lifecycle, signals to create deliveries
deliveries/    # Delivery scheduling, farmer updates, customer tracking
payments/      # Payment records, provider integration hooks, webhooks
ruralmarknet/  # Project settings, root URL configuration, ASGI/WSGI
locale/        # Translation source files (English, Hindi)
static/        # Tailwind build placeholder and static assets
templates/     # Base layout, shared includes
```

## Getting Started

1. **Clone & configure environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Create environment variables (optional)**
   Create a `.env` file (or configure your environment) with keys such as:
   ```env
   DJANGO_SECRET_KEY=replace-me
   DJANGO_DEBUG=1
   STRIPE_API_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   PAYPAL_CLIENT_ID=...
   PAYPAL_CLIENT_SECRET=...
   ```

3. **Apply migrations and create a superuser**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createcachetable
   python manage.py createsuperuser
   ```

4. **Install Tailwind and build assets**
   ```powershell
   python manage.py tailwind install
   python manage.py tailwind build
   ```

5. **Run the development server**
   ```powershell
   python manage.py runserver
   ```

6. **Access the app**
   - Customer storefront: http://127.0.0.1:8000/
   - Admin dashboard: http://127.0.0.1:8000/admin/

## Payments

`payments/services.py` contains provider-specific entry points:
- **Stripe**: replace the placeholder implementation with `stripe.checkout.Session.create` and configure webhook secrets.
- **PayPal**: swap the mocked redirect URL with a live order creation call using `paypalrestsdk` or REST API fetches.

Webhook handling is scaffolded via `payments.views.StripeWebhookView`; secure it with signature verification before production use.

## Internationalisation

- Enable new strings with `{% trans %}` or `gettext_lazy`.
- Extract translation catalogs:
  ```powershell
  django-admin makemessages -l en -l hi
  django-admin compilemessages
  ```
- Update `locale/hi/LC_MESSAGES/django.po` with approved translations.

## Testing

Run the Django test suite:
```powershell
python manage.py test
```

Included tests cover models, forms, and primary views across all apps. Extend with integration tests for ordering and payment flows as business rules evolve.

## Deployment Notes

- Configure environment variables for database, cache (Redis), and payment providers.
- Switch to PostgreSQL by setting `DJANGO_DB_ENGINE=django.db.backends.postgresql` and providing credentials.
- Add `gunicorn`/`uvicorn` for production servers and enable HTTPS via a proxy (nginx, Caddy, etc.).
- Consider Dockerisation: create a `Dockerfile` plus `docker-compose.yml` with web, worker (Celery), and Redis services.

## Future Enhancements

- Expose a REST API using Django REST Framework for mobile clients.
- Integrate real-time order status updates via WebSockets.
- Add farmer analytics dashboards (sales trends, delivery metrics).
- Support media storage on S3 or Cloudinary for product imagery.
