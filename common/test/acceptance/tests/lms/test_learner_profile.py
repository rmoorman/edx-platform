# -*- coding: utf-8 -*-
"""
End-to-end tests for Student's Profile Page.
"""
from datetime import datetime
from bok_choy.web_app_test import WebAppTest

from ...pages.lms.account_settings import AccountSettingsPage
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.learner_profile import LearnerProfilePage
from ...pages.lms.dashboard import DashboardPage

from ..helpers import EventsTestMixin


class LearnerProfilePageTest(EventsTestMixin, WebAppTest):
    """
    Tests that verify Student's Profile Page.
    """

    MY_USER = 1
    MY_USER_NAME = 'user1'
    MY_USER_EMAIL = 'user1@edx.org'

    OTHER_USER = 2
    OTHER_USER_NAME = 'user2'
    OTHER_USER_EMAIL = 'user2@edx.org'

    PRIVACY_PUBLIC = 'all_users'
    PRIVACY_PRIVATE = 'private'

    PUBLIC_PROFILE_FIELDS = ['username', 'country', 'language_proficiencies', 'bio']
    PRIVATE_PROFILE_FIELDS = ['username']

    PUBLIC_PROFILE_EDITABLE_FIELDS = ['country', 'language_proficiencies', 'bio']

    def setUp(self):
        """
        Initialize pages.
        """
        super(LearnerProfilePageTest, self).setUp()
        self.log_in_as_my_user()

    def log_in_as_my_user(self):
        """
        Log in as my user.
        """
        AutoAuthPage(self.browser, username=self.MY_USER_NAME, email=self.MY_USER_EMAIL).visit()

    def set_public_profile_fields_data(self, profile_page):
        """
        Fill in the public profile fields of a user.
        """
        profile_page.value_for_dropdown_field('language_proficiencies', 'English')
        profile_page.value_for_dropdown_field('country', 'United Kingdom')
        profile_page.value_for_textarea_field('bio', 'Nothing Special')

    def visit_profile_page(self, username, privacy=None):
        """
        Visits a user's profile page.
        """
        # Reset event tracking so that the tests only see events from
        # loading the profile page.
        self.reset_event_tracking()

        profile_page = LearnerProfilePage(self.browser, username)
        profile_page.visit()
        profile_page.wait_for_page()

        if privacy is not None:
            profile_page.privacy = privacy

            if privacy == self.PRIVACY_PUBLIC:
                self.set_public_profile_fields_data(profile_page)

        return profile_page

    def set_birth_year(self, birth_year):
        """
        Set birth year for the current user to the specified value.
        """
        account_settings_page = AccountSettingsPage(self.browser)
        account_settings_page.visit()
        account_settings_page.wait_for_page()
        self.assertEqual(
            account_settings_page.value_for_dropdown_field('year_of_birth', str(birth_year)),
            str(birth_year)
        )

    def verify_profile_forced_private_message(self, birth_year, message=None):
        """
        Verify age limit messages for a user.
        """
        self.set_birth_year(birth_year=birth_year if birth_year is not None else "")
        profile_page = self.visit_profile_page(self.MY_USER_NAME)
        self.assertTrue(profile_page.privacy_field_visible)
        self.assertEqual(profile_page.age_limit_message_present, message is not None)
        self.assertIn(message, profile_page.profile_forced_private_message)

    def verify_profile_page_view_event(self, profile_user_id, visibility=None, requires_parental_consent=False):
        """
        Verifies that the correct view event was captured for the profile page.
        """
        self.verify_browser_events(
            u"edx.user.settings.viewed",
            [{
                u"user_id": int(profile_user_id),
                u"page": u"profile",
                u"visibility": unicode(visibility),
                u"requires_parental_consent": requires_parental_consent,
            }]
        )

    def test_dashboard_learner_profile_link(self):
        """
        Scenario: Verify that my profile link is present on dashboard page and we can navigate to correct page.

        Given that I am a registered user.
        When I go to Dashboard page.
        And I click on username dropdown.
        Then I see My Profile link in the dropdown menu.
        When I click on My Profile link.
        Then I will be navigated to My Profile page.
        """
        dashboard_page = DashboardPage(self.browser)
        dashboard_page.visit()
        dashboard_page.click_username_dropdown()
        self.assertTrue('My Profile' in dashboard_page.username_dropdown_link_text)
        dashboard_page.click_my_profile_link()
        my_profile_page = LearnerProfilePage(self.browser, self.MY_USER_NAME)
        my_profile_page.wait_for_page()

    def test_fields_on_my_private_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own private profile.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to private.
        And I reload the page.
        Then I should see the profile visibility selector dropdown.
        Then I see some of the profile fields are shown.
        """
        profile_page = self.visit_profile_page(self.MY_USER_NAME, privacy=self.PRIVACY_PRIVATE)

        self.assertTrue(profile_page.privacy_field_visible)
        self.assertEqual(profile_page.visible_fields, self.PRIVATE_PROFILE_FIELDS)

        self.verify_profile_page_view_event(self.MY_USER, visibility=self.PRIVACY_PRIVATE)

    def test_fields_on_my_public_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at her own public profile.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to public.
        And I reload the page.
        Then I should see the profile visibility selector dropdown.
        Then I see all the profile fields are shown.
        And `location`, `language` and `about me` fields are editable.
        """
        profile_page = self.visit_profile_page(self.MY_USER_NAME, privacy=self.PRIVACY_PUBLIC)

        self.assertTrue(profile_page.privacy_field_visible)
        self.assertEqual(profile_page.visible_fields, self.PUBLIC_PROFILE_FIELDS)

        self.assertEqual(profile_page.editable_fields, self.PUBLIC_PROFILE_EDITABLE_FIELDS)

        self.verify_profile_page_view_event(self.MY_USER, visibility=self.PRIVACY_PUBLIC)

    def test_fields_on_others_private_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at another user's private profile.

        Given that I am a registered user.
        And I visit others private profile page.
        Then I shouldn't see the profile visibility selector dropdown.
        Then I see some of the profile fields are shown.
        """
        other_user_id = self._initialize_other_user(privacy=self.PRIVACY_PRIVATE)
        self.log_in_as_my_user()
        profile_page = self.visit_profile_page(self.OTHER_USER_NAME)

        self.assertFalse(profile_page.privacy_field_visible)
        self.assertEqual(profile_page.visible_fields, self.PRIVATE_PROFILE_FIELDS)
        self.verify_profile_page_view_event(other_user_id, visibility=self.PRIVACY_PRIVATE)

    def test_fields_on_others_public_profile(self):
        """
        Scenario: Verify that desired fields are shown when looking at another user's public profile.

        Given that I am a registered user.
        And I visit others public profile page.
        Then I shouldn't see the profile visibility selector dropdown.
        Then all the profile fields are shown.
        Then I shouldn't see the profile visibility selector dropdown.
        Also `location`, `language` and `about me` fields are not editable.
        """
        other_user_id = self._initialize_other_user(privacy=self.PRIVACY_PUBLIC)
        self.log_in_as_my_user()
        profile_page = self.visit_profile_page(self.OTHER_USER_NAME)
        profile_page.wait_for_public_fields()
        self.assertFalse(profile_page.privacy_field_visible)
        fields_to_check = self.PUBLIC_PROFILE_FIELDS
        self.assertEqual(profile_page.visible_fields, fields_to_check)
        self.assertEqual(profile_page.editable_fields, [])
        self.verify_profile_page_view_event(other_user_id, visibility=self.PRIVACY_PUBLIC)

    def _initialize_other_user(self, privacy=None):
        """
        Initialize the profile page for the other test user
        """
        if privacy is None:
            privacy = self.PRIVACY_PUBLIC

        # Log the user in
        other_auto_auth_page = AutoAuthPage(
            self.browser,
            username=self.OTHER_USER_NAME,
            email=self.OTHER_USER_EMAIL
        ).visit()
        other_user_id = other_auto_auth_page.get_user_id()

        # Set the user's birth year and privacy policy
        self.set_birth_year(birth_year=1990)
        self.visit_profile_page(self.OTHER_USER_NAME, privacy=privacy)

        return other_user_id

    def _test_dropdown_field(self, profile_page, field_id, new_value, displayed_value, mode):
        """
        Test behaviour of a dropdown field.
        """
        profile_page.value_for_dropdown_field(field_id, new_value)
        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

        self.browser.refresh()
        profile_page.wait_for_page()

        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

    def _test_textarea_field(self, profile_page, field_id, new_value, displayed_value, mode):
        """
        Test behaviour of a textarea field.
        """
        profile_page.value_for_textarea_field(field_id, new_value)
        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

        self.browser.refresh()
        profile_page.wait_for_page()

        self.assertEqual(profile_page.get_non_editable_mode_value(field_id), displayed_value)
        self.assertTrue(profile_page.mode_for_field(field_id), mode)

    def test_country_field(self):
        """
        Test behaviour of `Country` field.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to public and set default values for public fields.
        Then I set country value to `Pakistan`.
        Then displayed country should be `Pakistan` and country field mode should be `display`
        And I reload the page.
        Then displayed country should be `Pakistan` and country field mode should be `display`
        And I make `country` field editable
        Then `country` field mode should be `edit`
        And `country` field icon should be visible.
        """
        profile_page = self.visit_profile_page(self.MY_USER_NAME, privacy=self.PRIVACY_PUBLIC)
        self._test_dropdown_field(profile_page, 'country', 'Pakistan', 'Pakistan', 'display')

        profile_page.make_field_editable('country')
        self.assertTrue(profile_page.mode_for_field('country'), 'edit')

        self.assertTrue(profile_page.field_icon_present('country'))

    def test_language_field(self):
        """
        Test behaviour of `Language` field.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to public and set default values for public fields.
        Then I set language value to `Urdu`.
        Then displayed language should be `Urdu` and language field mode should be `display`
        And I reload the page.
        Then displayed language should be `Urdu` and language field mode should be `display`
        Then I set empty value for language.
        Then displayed language should be `Add language` and language field mode should be `placeholder`
        And I reload the page.
        Then displayed language should be `Add language` and language field mode should be `placeholder`
        And I make `language` field editable
        Then `language` field mode should be `edit`
        And `language` field icon should be visible.
        """
        profile_page = self.visit_profile_page(self.MY_USER_NAME, privacy=self.PRIVACY_PUBLIC)
        self._test_dropdown_field(profile_page, 'language_proficiencies', 'Urdu', 'Urdu', 'display')
        self._test_dropdown_field(profile_page, 'language_proficiencies', '', 'Add language', 'placeholder')

        profile_page.make_field_editable('language_proficiencies')
        self.assertTrue(profile_page.mode_for_field('language_proficiencies'), 'edit')

        self.assertTrue(profile_page.field_icon_present('language_proficiencies'))

    def test_about_me_field(self):
        """
        Test behaviour of `About Me` field.

        Given that I am a registered user.
        And I visit My Profile page.
        And I set the profile visibility to public and set default values for public fields.
        Then I set about me value to `Eat Sleep Code`.
        Then displayed about me should be `Eat Sleep Code` and about me field mode should be `display`
        And I reload the page.
        Then displayed about me should be `Eat Sleep Code` and about me field mode should be `display`
        Then I set empty value for about me.
        Then displayed about me should be `Tell other edX learners a little about yourself: where you live,
        what your interests are, why you're taking courses on edX, or what you hope to learn.` and about me
        field mode should be `placeholder`
        And I reload the page.
        Then displayed about me should be `Tell other edX learners a little about yourself: where you live,
        what your interests are, why you're taking courses on edX, or what you hope to learn.` and about me
        field mode should be `placeholder`
        And I make `about me` field editable
        Then `about me` field mode should be `edit`
        """
        placeholder_value = (
            "Tell other edX learners a little about yourself: where you live, what your interests are, "
            "why you're taking courses on edX, or what you hope to learn."
        )

        profile_page = self.visit_profile_page(self.MY_USER_NAME, privacy=self.PRIVACY_PUBLIC)
        self._test_textarea_field(profile_page, 'bio', 'Eat Sleep Code', 'Eat Sleep Code', 'display')
        self._test_textarea_field(profile_page, 'bio', '', placeholder_value, 'placeholder')

        profile_page.make_field_editable('bio')
        self.assertTrue(profile_page.mode_for_field('bio'), 'edit')

    def test_birth_year_not_set(self):
        """
        Verify message if birth year is not set.

        Given that I am a registered user.
        And birth year is not set for the user.
        And I visit my profile page.
        Then I should see a message that the profile is private until the year of birth is set.
        """
        message = "You must specify your birth year before you can share your full profile."
        self.verify_profile_forced_private_message(None, message=message)
        self.verify_profile_page_view_event(
            self.MY_USER,
            visibility=self.PRIVACY_PRIVATE,
            requires_parental_consent=True
        )

    def test_user_is_under_age(self):
        """
        Verify message if user is under age.

        Given that I am a registered user.
        And birth year is set so that age is less than 13.
        And I visit my profile page.
        Then I should see a message that the profile is private as I am under thirteen.
        """
        under_age_birth_year = datetime.now().year - 10
        self.verify_profile_forced_private_message(
            under_age_birth_year,
            message='You must be over 13 to share a full profile.'
        )
        self.verify_profile_page_view_event(
            self.MY_USER,
            visibility=self.PRIVACY_PRIVATE,
            requires_parental_consent=True
        )
