import os
import glob

old_str = '''          <div class="nav-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            <span class="badge">2</span>
          </div>'''

new_str = '''          <div id="notification-container" style="position: relative;">
            <div class="nav-icon" id="notification-btn" style="cursor: pointer;">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
              <span class="badge">2</span>
            </div>
            <div class="dropdown-menu" id="notification-dropdown" style="width: 320px; right: -10px; padding: 0;">
              <div class="dropdown-header" style="border-bottom: 1px solid var(--border); padding: 16px;">
                <div class="name" style="font-size: 14px;">Notifications</div>
              </div>
              <div style="padding: 16px; font-size: 14px; color: var(--text); border-bottom: 1px solid var(--border);">
                <div style="font-weight: 600; margin-bottom: 4px; color: var(--accent);">New Course Available</div>
                <div class="muted" style="line-height: 1.4;">Advanced Machine Learning is now open for enrollment.</div>
                <div class="muted" style="font-size: 12px; margin-top: 8px;">2 hours ago</div>
              </div>
              <div style="padding: 16px; font-size: 14px; color: var(--text);">
                <div style="font-weight: 600; margin-bottom: 4px; color: var(--accent);">Forum Reply</div>
                <div class="muted" style="line-height: 1.4;">Dr. Turing replied to your topic in Philosophy.</div>
                <div class="muted" style="font-size: 12px; margin-top: 8px;">5 hours ago</div>
              </div>
              </div>
            </div>
          </div>'''

files = glob.glob('backend/templates/*.html')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if old_str in content:
        content = content.replace(old_str, new_str)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Updated {f}')