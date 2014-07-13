from django.conf.urls import patterns, url, include

from brambling.forms.user import (
    FloppyAuthenticationForm,
    FloppyPasswordResetForm,
    FloppySetPasswordForm,
)
from brambling.models import Discount
from brambling.views.orders import (
    AddToCartView,
    RemoveFromCartView,
    UseDiscountView,
    ShopView,
    AttendeeBasicDataView,
    RemoveAttendeeView,
    AttendeeItemView,
    AttendeeHousingView,
    SurveyDataView,
    HostingView,
    OrderSummaryView,
)
from brambling.views.core import (
    UserDashboardView,
    SplashView,
)
from brambling.views.organizer import (
    EventCreateView,
    EventSummaryView,
    EventUpdateView,
    ItemListView,
    item_form,
    DiscountListView,
    discount_form,
    AttendeeFilterView,
    OrderFilterView,
    OrderDetailView,
)
from brambling.views.user import (
    PersonView,
    HomeView,
    SignUpView,
    EmailConfirmView,
    send_confirmation_email_view,
    CreditCardAddView,
    CreditCardDeleteView,
)
from brambling.views.utils import split_view, route_view, get_event_or_404


urlpatterns = patterns('',
    url(r'^$',
        split_view(lambda r, *a, **k: r.user.is_authenticated(),
                   UserDashboardView.as_view(),
                   SplashView.as_view()),
        name="brambling_dashboard"),
    url(r'^create/$',
        EventCreateView.as_view(),
        name="brambling_event_create"),

    url(r'^login/$',
        'django.contrib.auth.views.login',
        {'authentication_form': FloppyAuthenticationForm},
        name='login'),
    url(r'^password_reset/$',
        'django.contrib.auth.views.password_reset',
        {'password_reset_form': FloppyPasswordResetForm},
        name='password_reset'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'set_password_form': FloppySetPasswordForm},
        name='password_reset_confirm'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^signup/$',
        SignUpView.as_view(),
        name="brambling_signup"),
    url(r'^email_confirm/send/$',
        send_confirmation_email_view,
        name="brambling_email_confirm_send"),
    url(r'^email_confirm/(?P<pkb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        EmailConfirmView.as_view(),
        name="brambling_email_confirm"),

    url(r'^profile/$',
        PersonView.as_view(),
        name="brambling_user_profile"),
    url(r'^profile/card/add/$',
        CreditCardAddView.as_view(),
        name="brambling_user_card_add"),
    url(r'^profile/card/delete/(?P<pk>\d+)/$',
        CreditCardDeleteView.as_view(),
        name="brambling_user_card_delete"),
    url(r'^home/$',
        HomeView.as_view(),
        name="brambling_home"),

    url(r'^(?P<slug>[\w-]+)/$',
        route_view(lambda r, *a, **k: get_event_or_404(k['slug']
                                                       ).editable_by(r.user),
                   'summary/',
                   'shop/'),
        name="brambling_event_root"),
    url(r'^(?P<event_slug>[\w-]+)/order/shop/$',
        ShopView.as_view(),
        name="brambling_event_shop"),
    url(r'^(?P<event_slug>[\w-]+)/order/add/(?P<pk>\d+)/$',
        AddToCartView.as_view(),
        name="brambling_event_shop_add"),
    url(r'^(?P<event_slug>[\w-]+)/order/remove/(?P<pk>\d+)/$',
        RemoveFromCartView.as_view(),
        name="brambling_event_shop_remove"),

    url(r'^(?P<event_slug>[\w-]+)/order/attendee_items/',
        AttendeeItemView.as_view(),
        name="brambling_event_attendee_items"),
    url(r'^(?P<event_slug>[\w-]+)/order/attendees/add/$',
        AttendeeBasicDataView.as_view(),
        name="brambling_event_attendee_add"),
    url(r'^(?P<event_slug>[\w-]+)/order/attendees/(?P<pk>\d+)/$',
        AttendeeBasicDataView.as_view(),
        name="brambling_event_attendee_edit"),
    url(r'^(?P<event_slug>[\w-]+)/order/attendees/(?P<pk>\d+)/delete/$',
        RemoveAttendeeView.as_view(),
        name="brambling_event_attendee_delete"),

    url(r'^(?P<event_slug>[\w-]+)/order/housing_data/$',
        AttendeeHousingView.as_view(),
        name='brambling_event_attendee_housing'),
    url(r'^(?P<event_slug>[\w-]+)/order/survey/$',
        SurveyDataView.as_view(),
        name='brambling_event_survey'),
    url(r'^(?P<event_slug>[\w-]+)/order/hosting/$',
        HostingView.as_view(),
        name='brambling_event_hosting'),
    url(r'^(?P<event_slug>[\w-]+)/order/summary/$',
        OrderSummaryView.as_view(),
        name="brambling_event_order_summary"),
    url(r'^(?P<event_slug>[\w-]+)/order/discount/use/(?P<discount>{})/$'.format(Discount.CODE_REGEX),
        UseDiscountView.as_view(),
        name="brambling_event_use_discount"),

    url(r'^(?P<slug>[\w-]+)/summary/$',
        EventSummaryView.as_view(),
        name="brambling_event_summary"),
    url(r'^(?P<slug>[\w-]+)/edit/$',
        EventUpdateView.as_view(),
        name="brambling_event_update"),
    url(r'^(?P<event_slug>[\w-]+)/items/$',
        ItemListView.as_view(),
        name="brambling_item_list"),
    url(r'^(?P<event_slug>[\w-]+)/items/create/$',
        item_form,
        name="brambling_item_create"),
    url(r'^(?P<event_slug>[\w-]+)/items/(?P<pk>\d+)/$',
        item_form,
        name="brambling_item_update"),
    url(r'^(?P<event_slug>[\w-]+)/attendees/$',
        AttendeeFilterView.as_view(),
        name="brambling_event_attendees"),
    url(r'^(?P<event_slug>[\w-]+)/orders/$',
        OrderFilterView.as_view(),
        name="brambling_event_orders"),
    url(r'^(?P<event_slug>[\w-]+)/orders/(?P<pk>\d+)/$',
        OrderDetailView.as_view(),
        name="brambling_event_order_detail"),

    url(r'^(?P<event_slug>[\w-]+)/discount/$',
        DiscountListView.as_view(),
        name="brambling_discount_list"),
    url(r'^(?P<event_slug>[\w-]+)/discount/create/$',
        discount_form,
        name="brambling_discount_create"),
    url(r'^(?P<event_slug>[\w-]+)/discount/(?P<pk>\d+)/$',
        discount_form,
        name="brambling_discount_update"),
)
