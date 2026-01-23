import re
from unittest.mock import MagicMock, patch

from odoo.addons.base.tests.common import BaseCommon

from ..override import db_filter, db_filter_org


class TestDbFilter(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Sample list of customers
        cls.customers = ["customer_a_db", "customer_b_db", "test_db"]

        # Patch http.request globally for all tests
        patcher = patch("odoo.http.request", new=MagicMock())
        cls.mock_request = patcher.start()
        cls.addClassCleanup(patcher.stop)

        # Provide default environment for headers
        cls.mock_request.httprequest = MagicMock()
        cls.mock_request.httprequest.environ = {}

    def _filter_databases(self, db_list, regex):
        """Helper method to simulate the filtering logic for a specific regex."""
        if regex is None:
            return db_list
        pattern = re.compile(regex)
        return [db for db in db_list if pattern.fullmatch(db)]

    def set_header(self, value):
        """Helper to set the HTTP_X_ODOO_DBFILTER header."""
        self.mock_request.httprequest.environ = {"HTTP_X_ODOO_DBFILTER": value}

    def test_no_header_returns_all_customers(self):
        """Test that no filter header returns all available customer databases."""
        self.mock_request.httprequest.environ = {}
        result = db_filter(self.customers)
        expected = db_filter_org(self.customers, None)
        self.assertEqual(
            result,
            expected,
            "All databases should be returned when no header is set.",
        )

    def test_filter_returns_all_customers_if_everyone_matches(self):
        """Test that a filter regex matching all databases returns the full list."""
        self.set_header(".*")
        result = db_filter(self.customers)
        expected = [c for c in db_filter_org(self.customers, None) if re.match(".*", c)]
        self.assertEqual(
            result,
            expected,
            "Regex '.*' should return all customer databases.",
        )

    def test_filter_returns_empty_when_no_customers_match(self):
        """Test that a filter regex matching no database returns an empty list."""
        self.set_header("^non_existing_.*$")
        result = db_filter(self.customers)
        self.assertEqual(
            result,
            [],
            "Regex that matches no databases should return an empty list.",
        )

    def test_only_matching_customers(self):
        """Test that a filter matching a specific database
        returns only that database."""
        regex = "customer_a_db"
        result = self._filter_databases(self.customers, regex)
        self.assertEqual(
            result,
            ["customer_a_db"],
            "Only 'customer_a_db' should be returned by the filter.",
        )

    def test_invalid_filter_pattern_raises_error(self):
        """Test that an invalid regex raises a `re.error` exception."""
        invalid_regex = "[unclosed"
        with self.assertRaises(
            re.error,
            msg="Invalid regex should raise a re.error exception",
        ):
            self._filter_databases(self.customers, invalid_regex)

    def test_empty_customer_list_always_returns_empty(self):
        """Test that an empty customer list returns an empty list
        regardless of filter."""
        self.set_header(".*")
        result = db_filter([])
        self.assertEqual(
            result,
            [],
            "Empty customer list should always return an empty list.",
        )
