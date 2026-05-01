# GITHUB GUIDELINE

## Pull groupmate updates to your local

Use this command in your project folder:

```bash
git pull --rebase origin main
```

If there are conflicts, resolve them in files, then run:

```bash
git add .
git rebase --continue
```

---

## First-time setup (only once per machine/repo)

If you already cloned from GitHub, you can skip this section.

```bash
git remote add origin https://github.com/vincentlee001804/education_website.git
git branch -M main
git push -u origin main
```

If `origin` already exists and you need to change it:

```bash
git remote set-url origin https://github.com/vincentlee001804/education_website.git
```

---

## Daily workflow (recommended)

1. Pull latest changes first:

```bash
git pull --rebase origin main
```

2. Make your changes.
3. Commit:

```bash
git add .
git commit -m "your message"
```

4. Push:

```bash
git push origin main
```

---

## Common errors

### 1) `rejected (fetch first)` on push

Your local branch is behind remote.

```bash
git pull --rebase origin main
git push origin main
```

### 2) `remote origin already exists`

```bash
git remote set-url origin https://github.com/vincentlee001804/education_website.git
```

### 3) Need to overwrite remote with local (dangerous)

Use only if your team agrees:

```bash
git push --force-with-lease origin main
```

