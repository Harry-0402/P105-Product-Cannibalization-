import re

file_path = "Dashboard/index.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the direct LinkedIn header button with a nav link to the new creator page
old_str = '<a href="https://www.linkedin.com/in/harish-chavan-a4248738b" target="_blank" class="header-btn">\n                        <span>👤</span> Creator Profile\n                    </a>'
new_str = '<a href="#" class="header-btn nav-link" data-page="creator">\n                        <span>👤</span> Creator Profile\n                    </a>'

new_content = content.replace(old_str, new_str)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
