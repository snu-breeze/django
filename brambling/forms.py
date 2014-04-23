import datetime
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from zenaida.forms import inlineformset_factory
from zenaida import forms

from brambling.models import (Event, Person, Home, Item, ItemOption,
                              Discount, DanceStyle, EventType,
                              EventPerson, Date, EventHousing, PersonItem)
from brambling.utils import send_confirmation_email


class EventForm(forms.ModelForm):
    start_date = forms.DateField()
    end_date = forms.DateField()

    class Meta:
        model = Event
        exclude = ('dates', 'housing_dates', 'owner')
        widgets = {
            'country': forms.Select
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].initial = getattr(self.instance, 'start_date', datetime.date.today)
        self.fields['end_date'].initial = getattr(self.instance, 'end_date', datetime.date.today)

    def clean(self):
        cd = self.cleaned_data
        if cd['start_date'] > cd['end_date']:
            raise forms.ValidationError("End date must be before or equal to "
                                        "the start date.")
        return cd

    def save(self):
        instance = super(EventForm, self).save()
        if {'start_date', 'end_date'} & set(self.changed_data):
            cd = self.cleaned_data
            date_set = {cd['start_date'] + datetime.timedelta(n - 1) for n in
                        xrange((cd['end_date'] - cd['start_date']).days + 2)}
            seen = set(Date.objects.filter(date__in=date_set
                                           ).values_list('date', flat=True))
            Date.objects.bulk_create([
                Date(date=date) for date in date_set
                if date not in seen
            ])
            instance.housing_dates = Date.objects.filter(date__in=date_set)
            date_set.remove(cd['start_date'] - datetime.timedelta(1))
            instance.dates = Date.objects.filter(date__in=date_set)
        return instance


class FloppyAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=254)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)


class BasePersonForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(BasePersonForm, self).__init__(*args, **kwargs)

    def email_confirmation(self):
        if 'email' in self.changed_data:
            send_confirmation_email(self.instance, self.request,
                                    secure=self.request.is_secure())


class SignUpForm(BasePersonForm):
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = Person
        fields = ('email', 'name',)

    def clean_email(self):
        # Since Person.email is unique, this check is redundant,
        # but it sets a nicer error message.
        email = self.cleaned_data["email"]
        q = models.Q(email=email) | models.Q(confirmed_email=email)
        if Person._default_manager.filter(q).exists():
            raise forms.ValidationError(
                self.error_messages['duplicate_email'],
                code='duplicate_email',
            )
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self):
        person = super(SignUpForm, self).save(commit=False)
        person.set_password(self.cleaned_data["password1"])
        person.save()
        person.dance_styles = DanceStyle.objects.all()
        person.event_types = EventType.objects.all()
        self.email_confirmation()
        user = authenticate(email=self.cleaned_data['email'],
                            password=self.cleaned_data['password1'])
        login(self.request, user)
        return person


class PersonForm(BasePersonForm):
    class Meta:
        model = Person
        fields = ('email', 'name', 'nickname', 'phone', 'dance_styles',
                  'event_types', 'dietary_restrictions', 'ef_cause',
                  'ef_avoid', 'person_prefer', 'person_avoid',
                  'housing_prefer', 'other_needs')

    def save(self, commit=True):
        person = super(PersonForm, self).save(commit)
        if commit:
            self.email_confirmation()
        return person


class HomeForm(forms.ModelForm):
    class Meta:
        model = Home
        exclude = ()
        widgets = {
            'country': forms.Select
        }

    def __init__(self, person, *args, **kwargs):
        self.person = person
        super(HomeForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(HomeForm, self).save(commit)
        instance.residents.add(self.person)
        return instance


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ('event',)

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(ItemForm, self).__init__(*args, **kwargs)

    def _post_clean(self):
        super(ItemForm, self)._post_clean()
        self.instance.event = self.event


ItemOptionFormSet = inlineformset_factory(Item, ItemOption)


class DiscountForm(forms.ModelForm):
    generated_code = None

    class Meta:
        model = Discount
        exclude = ('event', 'items')

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(DiscountForm, self).__init__(*args, **kwargs)
        self.fields['item_option'].queryset = ItemOption.objects.filter(item__event=event)
        if not self.instance.code:
            self.generated_code = get_random_string(6)
            while Discount.objects.filter(event=self.event,
                                          code=self.generated_code).exists():
                self.generated_code = get_random_string(6)
            self.fields['code'].initial = self.generated_code

    def _post_clean(self):
        super(DiscountForm, self)._post_clean()
        self.instance.event = self.event
        try:
            self.instance.validate_unique()
        except forms.ValidationError as e:
            self._update_errors(e)


class ReservationForm(forms.ModelForm):
    """Lets a person choose item options to buy."""
    option_id = forms.IntegerField()

    class Meta:
        model = PersonItem
        fields = ()

    def __init__(self, buyer, item_option, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)
        self.buyer = buyer
        self.item_option = item_option
        self.fields['option_id'].initial = item_option.id

    def clean(self):
        cleaned_data = super(ReservationForm, self).clean()
        if self.item_option.id != cleaned_data.get('option_id'):
            raise forms.ValidationError("Be sure not to fiddle with the HTML code.")
        return cleaned_data

    def _post_clean(self):
        super(ReservationForm, self)._post_clean()
        self.instance.buyer = self.buyer
        self.instance.item_option = self.item_option
        self.instance.owner = None
        self.instance.status = PersonItem.RESERVED


class PersonItemForm(forms.ModelForm):
    class Meta:
        model = PersonItem
        fields = ('owner',)

    def __init__(self, event, housing_dates, user, data=None, files=None,
                 *args, **kwargs):
        self.event = event
        self.housing_dates = housing_dates
        self.user = user
        super(PersonItemForm, self).__init__(data, files, *args, **kwargs)
        self.item = self.instance.item_option.item
        self.buyer = self.instance.buyer
        self.owner = self.instance.owner
        self.initial['owner'] = self.owner or self.buyer

        if self.item.category == Item.PASS:
            self.owner_forms = {
                'eventperson': EventPersonForm(
                    person=self.owner,
                    event=self.event,
                    data=data,
                    files=files,
                    prefix=self.prefix + '-owner-eventperson'
                ),
                'guest': GuestForm(
                    person=self.owner,
                    with_defaults=False,
                    event=self.event,
                    housing_dates=housing_dates,
                    data=data,
                    files=files,
                    prefix=self.prefix + '-owner-guest'
                )
            }
            if self.user == self.owner:
                self.owner_forms['host'] = HostingForm(
                    home=self.owner.home,
                    event=self.event,
                    housing_dates=housing_dates,
                    data=data,
                    files=files,
                    prefix=self.prefix + '-owner-host'
                )
            else:
                self.buyer_forms = {
                    'eventperson': EventPersonForm(
                        person=self.buyer,
                        event=self.event,
                        data=data,
                        files=files,
                        prefix=self.prefix + '-buyer-eventperson'
                    ),
                    'guest': GuestForm(
                        person=self.buyer,
                        with_defaults=True,
                        event=self.event,
                        housing_dates=housing_dates,
                        data=data,
                        files=files,
                        prefix=self.prefix + '-buyer-guest'
                    ),
                    'host': HostingForm(
                        home=self.buyer.home,
                        event=self.event,
                        housing_dates=housing_dates,
                        data=data,
                        files=files,
                        prefix=self.prefix + '-buyer-host'
                    )
                }

    def is_valid(self):
        valid = super(PersonItemForm, self).is_valid()
        if valid and self.item.category == Item.Pass:
            valid = self.eventpersonform.is_valid()
            if valid:
                housing = self.eventpersonform.cleaned_data['housing']
                if housing == EventPerson.NEED:
                    valid = self.guestform.is_valid()
                elif housing == EventPerson.HOST:
                    valid = self.hostform.is_valid()
        return valid


class PersonItemFormSet(forms.models.BaseModelFormSet):
    def __init__(self, event, user, *args, **kwargs):
        self.event = event
        self.user = user
        self.housing_dates = event.housing_dates.all()
        super(PersonItemFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs.update({
            'event': self.event,
            'housing_dates': self.housing_dates,
            'user': self.user,
        })
        return super(PersonItemFormSet, self)._construct_form(i, **kwargs)


class EventPersonForm(forms.ModelForm):
    class Meta:
        model = EventPerson
        fields = ('car_spaces', 'bedtime', 'wakeup', 'housing')

    def __init__(self, person, event, *args, **kwargs):
        self.person = person
        self.event = event
        if person is None:
            instance = EventPerson(event=event)
        else:
            instance = EventPerson(person=person, event=event)
            try:
                instance = EventPerson.objects.get(person=person, event=event)
            except EventPerson.DoesNotExist:
                pass
        kwargs['instance'] = instance
        super(EventPersonForm, self).__init__(*args, **kwargs)


class GuestForm(forms.ModelForm):
    class Meta:
        model = EventPerson
        exclude = ('event', 'person', 'car_spaces',
                   'bedtime', 'wakeup', 'housing', 'event_pass')

    def __init__(self, person, event, housing_dates, with_defaults=True, *args, **kwargs):
        self.person = person
        self.event = event
        self.with_defaults = with_defaults
        if person is None:
            instance = EventPerson(event=event)
        else:
            instance = EventPerson(person=person, event=event)
            try:
                instance = EventPerson.objects.get(person=person, event=event)
            except EventPerson.DoesNotExist:
                pass
        kwargs['instance'] = instance
        super(GuestForm, self).__init__(*args, **kwargs)
        if with_defaults and person is not None:
            self.fields['save_as_defaults'] = forms.BooleanField(initial=True)
            if self.instance.pk is None:
                self.initial.update({
                    'ef_cause': person.ef_cause.all(),
                    'ef_avoid': person.ef_avoid.all(),
                    'person_prefer': person.person_prefer.all(),
                    'person_avoid': person.person_avoid.all(),
                    'housing_prefer': person.housing_prefer.all(),
                    'other_needs': person.other_needs,
                })
                self.instance.event = event
                self.instance.person = person
        self.fields['nights'].queryset = housing_dates

    def save(self):
        instance = super(GuestForm, self).save()
        if self.with_defaults and self.cleaned_data['save_as_defaults']:
            self.owner.ef_cause = instance.ef_cause.all()
            self.owner.ef_avoid = instance.ef_avoid.all()
            self.owner.person_prefer = instance.person_prefer.all()
            self.owner.person_avoid = instance.person_avoid.all()
            self.owner.housing_prefer = instance.housing_prefer.all()
            self.owner.other_needs = instance.other_needs
            self.owner.save()
        return instance


class HostingForm(forms.ModelForm):
    save_as_defaults = forms.BooleanField(initial=True)

    class Meta:
        model = EventHousing
        exclude = ('event', 'home')

    def __init__(self, home, event, housing_dates, *args, **kwargs):
        self.home = home
        kwargs['instance'] = EventHousing.objects.filter(
            event=event,
            home=home
        ).first()
        super(HostingForm, self).__init__(*args, **kwargs)
        if self.instance.pk is None and home is not None:
            self.initial.update({
                'ef_present': home.ef_present.all(),
                'ef_avoid': home.ef_avoid.all(),
                'person_prefer': home.person_prefer.all(),
                'person_avoid': home.person_avoid.all(),
                'housing_categories': home.housing_categories.all(),
            })
            self.instance.event = event
            self.instance.home = home
        self.fields['nights'].queryset = housing_dates

    def save(self):
        instance = super(HostingForm, self).save()
        if self.cleaned_data['save_as_defaults']:
            self.home.ef_present = instance.ef_present.all()
            self.home.ef_avoid = instance.ef_avoid.all()
            self.home.person_prefer = instance.person_prefer.all()
            self.home.person_avoid = instance.person_avoid.all()
            self.home.housing_categories = instance.housing_categories.all()
            self.home.save()
        return instance
