#!/usr/bin/env python3
"""Toggle the current TV session's service mode; no root privileges needed."""
import sys
import window_state
value=sys.argv[1] if len(sys.argv)>1 else 'toggle'
if value not in ('toggle','on','off'):
    raise SystemExit('Use toggle, on, or off')
enabled=not window_state.service_enabled() if value=='toggle' else value=='on'
window_state.set_service_mode(enabled)
print('Service mode on' if enabled else 'TV mode locked')
