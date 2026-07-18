import re

file_path = "Dashboard/index.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_block = """<div class="header-actions">
                    <a href="https://github.com/Harry-0402/P105-Product-Cannibalization-/tree/main" target="_blank" class="header-btn">
                        <span>📄</span> Documents
                    </a>
                    <a href="https://github.com/Harry-0402/P105-Product-Cannibalization-" target="_blank" class="header-btn">
                        <span><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg></span> GitHub Repo
                    </a>
                    <a href="https://www.linkedin.com/in/harish-chavan-a4248738b" target="_blank" class="header-btn">
                        <span>👤</span> Creator Profile
                    </a>
                </div>"""

pattern = re.compile(r'<div class="header-actions">\s*<a href="https://github\.com/Harry-0402/P105-Product-Cannibalization-" target="_blank" class="header-btn">\s*<span><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-\.94-2\.61c3\.14-\.35 6\.44-1\.54 6\.44-7A5\.44 5\.44 0 0 0 20 4\.77 5\.07 5\.07 0 0 0 19\.91 1S18\.73\.65 16 2\.48a13\.38 13\.38 0 0 0-7 0C6\.27\.65 5\.09 1 5\.09 1A5\.07 5\.07 0 0 0 5 4\.77a5\.44 5\.44 0 0 0-1\.5 3\.78c0 5\.42 3\.3 6\.61 6\.44 7A3\.37 3\.37 0 0 0 9 18\.13V22"></path></svg></span> GitHub Repo\s*</a>\s*<a href="https://github\.com/Harry-0402/P105-Product-Cannibalization-/tree/main" target="_blank" class="header-btn">\s*<span>📄</span> Documents\s*</a>\s*</div>')

matches = pattern.findall(content)
print(f"Found {len(matches)} occurrences to replace.")

new_content = pattern.sub(new_block, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
