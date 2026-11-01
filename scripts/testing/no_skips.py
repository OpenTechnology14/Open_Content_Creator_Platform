"""Pytest plugin for required security lanes: a skipped check cannot be green evidence."""


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter and reporter.stats.get("skipped"):
        reporter.write_line("Required security lane contains skipped tests", red=True)
        session.exitstatus = 1
