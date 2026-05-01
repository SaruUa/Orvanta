from django import forms


def _append_css_class(widget, class_name):
    existing_classes = widget.attrs.get('class', '').split()
    if class_name not in existing_classes:
        existing_classes.append(class_name)
    widget.attrs['class'] = ' '.join(existing_classes)


def apply_bootstrap_classes(fields):
    for field in fields.values():
        widget = field.widget

        if isinstance(widget, forms.CheckboxInput):
            _append_css_class(widget, 'form-check-input')
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            _append_css_class(widget, 'form-select')
        else:
            _append_css_class(widget, 'form-control')

        if field.required:
            widget.attrs.setdefault('aria-required', 'true')


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)
