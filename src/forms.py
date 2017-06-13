from wtforms.validators import DataRequired, Optional, Length
from wtforms import Form, BooleanField, StringField, PasswordField, validators, SelectMultipleField, IntegerField, FileField, HiddenField, TextAreaField
from wtforms.widgets import TextArea

class PersonForm(Form):

    name = StringField('NAME', validators=[DataRequired()])
    email = StringField('EMAIL', validators=[DataRequired(), validators.Email()])


class EntityForm(Form):

    name = StringField('NAME', validators=[DataRequired()])
    description = TextAreaField('DESCRIPTION', [validators.optional(), validators.length(max=1024)])
    serial = StringField('SERIAL')
    configs = SelectMultipleField('CONFIG FILES')


class ConfigForm(Form):

    name = StringField('NAME', validators=[DataRequired()])
    path = StringField('PATH /etc/opt/augment00/', validators=[DataRequired()])
    file_text = HiddenField('TEXT', [DataRequired()])

