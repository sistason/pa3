from django import forms
from django.forms.forms import NON_FIELD_ERRORS
#from models import Location
from pa3.settings import USER_TO_NAMES
from pa3.models import NewestNumberBatch
from django.utils.translation import ugettext


class FormWithNonFieldErrorExpansion:
    def __init__(self):
        self._errors = {}
        self.error_class = None

    def add_form_error(self, message):
        if not self._errors:
            self._errors = forms.util.ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)


class SubscribeForm(forms.Form, FormWithNonFieldErrorExpansion):
    choices_src = zip(USER_TO_NAMES.keys(), USER_TO_NAMES.keys())
    src = forms.ChoiceField(choices=choices_src)

    buf = forms.CharField(initial=5, max_length=5, 
                            widget=forms.TextInput(attrs={'size':'5'}))
    number = None

    def __init__(self, name, kwargs):
        super(SubscribeForm, self).__init__(**kwargs)
        self.success=[]
        if name == 'sms':
            self.fields['recipient'] = forms.CharField(max_length=100, 
            widget=forms.TextInput(attrs={'placeholder': ugettext('Your mobile number')}))
        elif name == 'mail':
            self.fields['recipient'] = forms.CharField(max_length=100, 
            widget=forms.TextInput(attrs={'placeholder': ugettext('Your mail address')}))
        elif name == 'xmpp':
            self.fields['recipient'] = forms.CharField(max_length=100, 
            widget=forms.TextInput(attrs={'placeholder': ugettext('Your XMPP-account')}))
        elif name == 'browser':
            pass
        else:
            del self
            return
        self.protocol = name
        # Populate number here, because earlier, ugettext defaults to wrong language
        self.fields['number'] = forms.CharField(max_length=10, widget=forms.TextInput(
                            attrs={'placeholder': ugettext('Your drawn number')}))


class BlacklistForm(forms.Form, FormWithNonFieldErrorExpansion):
    address = forms.CharField(max_length=100)

    #choices_proto_t = [i.protocol for i in ClientHandler.objects.all() if i.active]
    choices_proto_t = []
    choices_proto = zip(choices_proto_t, choices_proto_t)
    protocol = forms.ChoiceField(choices=choices_proto)
    success = []
