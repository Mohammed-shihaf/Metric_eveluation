"""Streamlit run panel with live progress and stdout streaming."""

from __future__ import print_function

import contextlib
import io
import time

import streamlit as st


class _LiveLog(io.StringIO):
    def __init__(self, box, max_lines=200, min_interval=0.4):
        super().__init__()
        self._box = box
        self._lines = []
        self._max = max_lines
        self._min_interval = min_interval
        self._last_render = 0.0

    def _render(self, force=False):
        now = time.time()
        if not force and (now - self._last_render) < self._min_interval:
            return
        self._last_render = now
        self._box.code("\n".join(self._lines[-40:]), language=None)

    def write(self, s):
        if not s:
            return 0
        super().write(s)
        for line in s.splitlines():
            if line.strip():
                self._lines.append(line.rstrip())
        if len(self._lines) > self._max:
            self._lines = self._lines[-self._max :]
        self._render()
        return len(s)

    def flush(self):
        self._render(force=True)


class _MultiRedirect(object):
    def __init__(self, *contexts):
        self._contexts = contexts

    def __enter__(self):
        for ctx in self._contexts:
            ctx.__enter__()
        return self

    def __exit__(self, *args):
        exc = None
        for ctx in reversed(self._contexts):
            if ctx.__exit__(*args):
                exc = True
        return exc


class RunPanel(object):
    """Context manager: st.status + progress + live log."""

    def __init__(self, title):
        self.title = title
        self._status = None
        self.bar = None
        self.status_line = None
        self.log_box = None
        self._log_stream = None
        self._result_state = None
        self._result_label = None

    def set_result(self, state, label=None):
        """Set final status outcome (complete, error, running). Used on clean exit."""
        self._result_state = state
        self._result_label = label

    def __enter__(self):
        self._status = st.status(self.title, expanded=True)
        self._status.__enter__()
        self.bar = st.progress(0.0)
        self.status_line = st.empty()
        self.detail_line = st.empty()
        self.log_box = st.empty()
        self._log_stream = _LiveLog(self.log_box)
        return self

    def progress(self, phase, current, total, branch="", message=""):
        total = max(int(total or 0), 1)
        current = min(max(int(current or 0), 0), total)
        self.bar.progress(min(current / total, 1.0))
        self.status_line.markdown(
            "**%s** — `%s` — **%d / %d** — %s"
            % (self.title, phase, current, total, branch or "—")
        )
        if message:
            self.detail_line.caption(message)
        else:
            self.detail_line.empty()

    def hold_until(self, start_ts, min_seconds, phase="Finalizing"):
        """Keep the panel alive until min_seconds elapsed from start_ts."""
        min_seconds = max(float(min_seconds or 0), 0.0)
        while True:
            elapsed = time.time() - start_ts
            if elapsed >= min_seconds:
                break
            self.bar.progress(min(elapsed / min_seconds, 1.0))
            self.status_line.markdown(
                "**%s** — `%s` — **%.0fs / %ds**"
                % (self.title, phase, elapsed, int(min_seconds))
            )
            time.sleep(0.5)
        self.bar.progress(1.0)

    def stdout_redirect(self):
        return contextlib.redirect_stdout(self._log_stream)

    def io_redirect(self):
        """Capture stdout and stderr into the live log panel."""
        return _MultiRedirect(
            contextlib.redirect_stdout(self._log_stream),
            contextlib.redirect_stderr(self._log_stream),
        )

    @property
    def log_lines(self):
        if self._log_stream:
            return list(self._log_stream._lines)
        return []

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self._status.update(label="%s — failed" % self.title, state="error")
        elif self._result_state:
            suffix = self._result_label or self._result_state
            self._status.update(
                label="%s — %s" % (self.title, suffix),
                state=self._result_state,
            )
        else:
            self._status.update(label="%s — complete" % self.title, state="complete")
        return self._status.__exit__(exc_type, exc, tb)
