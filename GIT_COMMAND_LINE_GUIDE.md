# Git Command Line - Step-by-Step Guide

## 📥 Step 1: Install Git

### Download and Install
1. Go to: **https://git-scm.com/download/win**
2. Download the installer (64-bit recommended)
3. Run the installer
4. Use these settings during installation:
   - ✅ Use default editor (or select your preferred editor)
   - ✅ Let Git decide the default branch name (will be "main")
   - ✅ Git from the command line and also from 3rd-party software
   - ✅ Use bundled OpenSSH
   - ✅ Use the OpenSSL library
   - ✅ Checkout Windows-style, commit Unix-style line endings
   - ✅ Use MinTTY (default terminal)
   - ✅ Default (fast-forward or merge)
   - ✅ Git Credential Manager
   - ✅ Enable file system caching
5. Click "Install"
6. **Restart your terminal/PowerShell after installation**

### Verify Installation
Open a new PowerShell window and run:
```powershell
git --version
```
You should see something like: `git version 2.43.0.windows.1`

---

## 🔧 Step 2: Configure Git (First Time Only)

Set your name and email (will appear in commits):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Verify configuration:
```powershell
git config --list
```

---

## 🔐 Step 3: Create GitHub Personal Access Token

**Important:** GitHub no longer accepts passwords for Git operations. You need a Personal Access Token (PAT).

1. Go to: **https://github.com/settings/tokens**
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `AWS Scraper - Git Access`
4. Set expiration: Choose your preference (30 days, 90 days, or No expiration)
5. Select scopes:
   - ✅ **repo** (Full control of private repositories)
   - This gives you all the permissions you need
6. Scroll down and click **"Generate token"**
7. **IMPORTANT:** Copy the token immediately and save it somewhere safe!
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to see it again!

---

## 📁 Step 4: Navigate to Your Project

Open PowerShell and navigate to your project directory:

```powershell
cd C:\DriveD\Work\Code
```

Verify you're in the right place:
```powershell
dir
```
You should see: README.md, setup.py, aws_scraper folder, etc.

---

## 🎯 Step 5: Initialize Git Repository

```powershell
git init
```

You should see: `Initialized empty Git repository in C:/DriveD/Work/Code/.git/`

---

## ✅ Step 6: Check What Will Be Committed

```powershell
git status
```

This shows all files that will be tracked. You should see:
- ✅ README.md
- ✅ .gitignore
- ✅ setup.py
- ✅ pyproject.toml
- ✅ requirements.txt
- ✅ aws_scraper/ folder
- ✅ config/ folder

You should NOT see (excluded by .gitignore):
- ❌ tests/
- ❌ LICENSE
- ❌ .env.example
- ❌ MANIFEST.in
- ❌ app.py, auth/, s3_operations/
- ❌ __pycache__/, *.pyc files

---

## 📦 Step 7: Stage All Files

```powershell
git add .
```

The `.` means "add all files" (respecting .gitignore)

Verify what's staged:
```powershell
git status
```

You should see files in green (staged for commit).

---

## 💬 Step 8: Create Your First Commit

```powershell
git commit -m "Initial commit: AWS Announcements Scraper v1.0.0

- Bilingual support (English and Chinese)
- Date-based filtering
- Multiple output formats (JSON, CSV, TXT, HTML)
- Robust error handling with retry logic
- Configurable timeouts and rate limiting"
```

You should see output like:
```
[main (root-commit) abc1234] Initial commit: AWS Announcements Scraper v1.0.0
 18 files changed, 2500 insertions(+)
 create mode 100644 README.md
 ...
```

---

## 🌐 Step 9: Create Repository on GitHub

1. Go to: **https://github.com/new**
2. Fill in:
   - **Repository name:** `aws-announcements-scraper`
   - **Description:** `Python web scraper for AWS China announcements with bilingual support`
   - **Public** or **Private:** Choose your preference
   - ❌ **DO NOT** check "Initialize this repository with a README"
   - ❌ **DO NOT** add .gitignore or license
3. Click **"Create repository"**

GitHub will show you a page with setup instructions. Ignore them - follow the steps below instead.

---

## 🔗 Step 10: Connect Local Repository to GitHub

Replace `YOUR-USERNAME` with your actual GitHub username:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/aws-announcements-scraper.git
```

Verify the remote was added:
```powershell
git remote -v
```

You should see:
```
origin  https://github.com/YOUR-USERNAME/aws-announcements-scraper.git (fetch)
origin  https://github.com/YOUR-USERNAME/aws-announcements-scraper.git (push)
```

---

## 🚀 Step 11: Push to GitHub

Make sure you're on the main branch:
```powershell
git branch -M main
```

Push your code:
```powershell
git push -u origin main
```

**You'll be prompted for credentials:**
- **Username:** Your GitHub username
- **Password:** **PASTE YOUR PERSONAL ACCESS TOKEN** (not your GitHub password!)

The token looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Note:** When you paste the token, you won't see any characters appear (for security). Just paste and press Enter.

You should see output like:
```
Enumerating objects: 25, done.
Counting objects: 100% (25/25), done.
Delta compression using up to 8 threads
Compressing objects: 100% (20/20), done.
Writing objects: 100% (25/25), 15.23 KiB | 1.52 MiB/s, done.
Total 25 (delta 2), reused 0 (delta 0), pack-reused 0
To https://github.com/YOUR-USERNAME/aws-announcements-scraper.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## 🎉 Step 12: Verify on GitHub

1. Go to: `https://github.com/YOUR-USERNAME/aws-announcements-scraper`
2. You should see:
   - ✅ README.md displays on the homepage
   - ✅ All your files (18 files)
   - ✅ Commit message: "Initial commit: AWS Announcements Scraper v1.0.0"
   - ✅ No unwanted files (tests/, LICENSE, etc.)

---

## 📝 Step 13: Add Repository Description and Topics

On your GitHub repository page:

1. Click the **⚙️ gear icon** next to "About" (top right)
2. Add description:
   ```
   Python web scraper for AWS China announcements with bilingual support, date filtering, and multiple output formats
   ```
3. Add topics (press Enter after each):
   - python
   - web-scraping
   - aws
   - scraper
   - beautifulsoup
   - cli-tool
   - aws-china
4. Click **"Save changes"**

---

## ✅ Done! Your Code is on GitHub!

Your repository is now live at:
```
https://github.com/YOUR-USERNAME/aws-announcements-scraper
```

---

## 🔄 Making Future Updates

When you make changes to your code:

### 1. Check what changed
```powershell
git status
```

### 2. Stage the changes
```powershell
# Stage all changes
git add .

# Or stage specific files
git add aws_scraper/main.py
```

### 3. Commit the changes
```powershell
git commit -m "Add new feature: XYZ"
```

### 4. Push to GitHub
```powershell
git push
```

---

## 🆘 Troubleshooting

### Problem: `git: command not found`
**Solution:** 
- Git is not installed or not in PATH
- Restart your terminal after installing Git
- Reinstall Git and make sure to select "Git from the command line and also from 3rd-party software"

### Problem: Authentication failed
**Solution:**
- Make sure you're using your Personal Access Token, NOT your password
- Check that your token has `repo` scope
- Generate a new token if the old one expired

### Problem: Too many files showing up
**Solution:**
- Make sure .gitignore is in the root folder
- Run: `git rm --cached -r .` then `git add .` to re-apply .gitignore

### Problem: `fatal: remote origin already exists`
**Solution:**
- Remove the remote: `git remote remove origin`
- Add it again: `git remote add origin https://github.com/YOUR-USERNAME/aws-announcements-scraper.git`

### Problem: Push rejected (non-fast-forward)
**Solution:**
- Someone else pushed changes, or you made changes on GitHub
- Pull first: `git pull origin main`
- Then push: `git push`

### Problem: Credential helper issues on Windows
**Solution:**
- Use Git Credential Manager (installed with Git for Windows)
- Or store credentials: `git config --global credential.helper store`
- Next time you push, enter your token, and it will be saved

---

## 📚 Useful Git Commands

```powershell
# View commit history
git log

# View commit history (one line per commit)
git log --oneline

# View changes before staging
git diff

# View changes after staging
git diff --staged

# Undo changes to a file (before staging)
git checkout -- filename.py

# Unstage a file (keep changes)
git reset HEAD filename.py

# View remote repository URL
git remote -v

# View current branch
git branch

# Create and switch to new branch
git checkout -b feature-branch

# Switch back to main branch
git checkout main

# Pull latest changes from GitHub
git pull

# Clone a repository
git clone https://github.com/USERNAME/REPO.git
```

---

## 🔐 Saving Your Token (Optional)

To avoid entering your token every time:

### Option 1: Git Credential Manager (Recommended - Windows)
Git for Windows includes this by default. After you enter your token once, it's saved securely in Windows Credential Manager.

### Option 2: Store credentials in Git config
```powershell
git config --global credential.helper store
```
Next time you push, enter your token. It will be saved in plain text in `~/.git-credentials`

**Security Note:** Only use this on your personal computer.

---

## 📞 Need Help?

- Git Documentation: https://git-scm.com/doc
- GitHub Docs: https://docs.github.com/en
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf

---

**Congratulations! You've successfully pushed your AWS Announcements Scraper to GitHub using Git! 🎊**
