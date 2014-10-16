"""Utility functions that combine steps to locate elements"""

import socket
import time
import urlparse

from selenium.common.exceptions import NoSuchElementException

from nose.tools import assert_true as nose_assert_true
from nose.tools import assert_false as nose_assert_false

# pylint:disable=missing-docstring,redefined-outer-name,redefined-builtin
# pylint:disable=invalid-name


class AssertContextManager():
    def __init__(self, step):
        self.step = step

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        step = self.step
        if traceback:
            if isinstance(value, AssertionError):
                error = AssertionError(self.step.sentence)
            else:
                sentence = "%s, failed because: %s" % (step.sentence, value)
                error = AssertionError(sentence)
            raise error, None, traceback


def assert_true(step, exp):
    with AssertContextManager(step):
        nose_assert_true(exp)


def assert_false(step, exp, msg=None):
    with AssertContextManager(step):
        nose_assert_false(exp, msg)


def element_id_by_label(browser, label):
    """Return the id of a label's for attribute"""
    for_id = browser.find_elements_by_xpath(str('//label[contains(., "%s")]' %
                                                label))
    if not for_id:
        return False
    return for_id[0].get_attribute('for')


## Field helper functions to locate select, textarea, and the other
## types of input fields (text, checkbox, radio)
def field_xpath(field, attribute):
    if field in ['select', 'textarea']:
        return './/%s[@%s="%%s"]' % (field, attribute)
    elif field == 'button':
        if attribute == 'value':
            return './/%s[contains(., "%%s")]' % (field, )
        else:
            return './/%s[@%s="%%s"]' % (field, attribute)
    elif field == 'option':
        return './/%s[@%s="%%s"]' % (field, attribute)
    else:
        return './/input[@%s="%%s"][@type="%s"]' % (attribute, field)


def find_button(browser, value):
    return find_field_with_value(browser, 'submit', value) or \
        find_field_with_value(browser, 'reset', value) or \
        find_field_with_value(browser, 'button', value) or \
        find_field_with_value(browser, 'image', value)


def find_field_with_value(browser, field, value):
    return find_field_by_id(browser, field, value) or \
        find_field_by_name(browser, field, value) or \
        find_field_by_value(browser, field, value)


def find_option(browser, select_name, option_name):
    # First, locate the select
    select_box = find_field(browser, 'select', select_name)
    assert select_box

    # Now locate the option
    option_box = find_field(select_box, 'option', option_name)
    if not option_box:
        # Locate by contents
        option_box = select_box.find_element_by_xpath(str(
            './/option[contains(., "%s")]' % option_name))
    return option_box


def find_field(browser, field, value):
    """Locate an input field of a given value

    This first looks for the value as the id of the element, then
    the name of the element, then a label for the element.

    """
    return find_field_by_id(browser, field, value) or \
        find_field_by_name(browser, field, value) or \
        find_field_by_label(browser, field, value)


def find_any_field(browser, field_types, field_name):
    """
    Find a field of any of the specified types.
    """

    for field_type in field_types:
        field = find_field(browser, field_type, field_name)
        if field:
            return field
    else:
        return False


def find_field_by_id(browser, field, id):
    xpath = field_xpath(field, 'id')
    elems = browser.find_elements_by_xpath(str(xpath % id))
    return elems[0] if elems else False


def find_field_by_name(browser, field, name):
    xpath = field_xpath(field, 'name')
    elems = browser.find_elements_by_xpath(str(xpath % name))
    return elems[0] if elems else False


def find_field_by_value(browser, field, name):
    xpath = field_xpath(field, 'value')
    elems = [elem for elem in browser.find_elements_by_xpath(str(xpath % name))
             if elem.is_displayed() and elem.is_enabled()]

    # sort by shortest first (most closely matching)
    if field == 'button':
        elems = sorted(elems, key=lambda elem: len(elem.text))
    else:
        elems = sorted(elems,
                       key=lambda elem: len(elem.get_attribute('value')))

    return elems[0] if elems else False


def find_field_by_label(browser, field, label):
    """Locate the control input that has a label pointing to it

    This will first locate the label element that has a label of the given
    name. It then pulls the id out of the 'for' attribute, and uses it to
    locate the element by its id.

    """
    for_id = element_id_by_label(browser, label)
    if not for_id:
        return False
    return find_field_by_id(browser, field, for_id)


def option_in_select(browser, select_name, option):
    """
    Returns the Element specified by @option or None

    Looks at the real <select> not the select2 widget, since that doesn't
    create the DOM until we click on it.
    """

    select = find_field(browser, 'select', select_name)
    assert select

    try:
        return select.find_element_by_xpath(str(
            './/option[normalize-space(text()) = "%s"]' % option))
    except NoSuchElementException:
        return None


def wait_for(func):
    """
    A decorator to invoke a function periodically until it returns a truthy
    value.
    """

    def wrapped(*args, **kwargs):
        timeout = kwargs.pop('timeout', 15)

        start = time.time()
        result = None

        while time.time() - start < timeout:
            result = func(*args, **kwargs)
            if result:
                break
            time.sleep(0.2)

        return result

    return wrapped
