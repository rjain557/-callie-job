# Callie Wells Portfolio Site

A single-file, zero-dependency portfolio site ready to deploy in 10 minutes. Drop it
into a free hosting service and you have a professional URL to put on your resume
and LinkedIn.

## Preview
Open `index.html` in any browser — that's it. No build step.

## How to add your project photos

1. Create a folder next to `index.html` called `images/`
2. Drop in 4 photos named:
   - `project-1.jpg`
   - `project-2.jpg`
   - `project-3.jpg`
   - `project-4.jpg`
3. Refresh the page — photos appear automatically

### Photo tips

- **Best:** Actual project photos you took or were allowed to take
- **Good:** "Before and after" compositions
- **Acceptable:** Inspiration/moodboard-style compositions you curated from
  public domain sources (Unsplash is free, credit not required for design portfolios)
- **Sizes:** Minimum 1200px wide, 1500px tall (portrait 4:5 ratio works best)
- **Format:** JPG is fine, PNG if transparency needed (not for photos)

## How to customize the text

Open `index.html` in any text editor (Notepad, VSCode, TextEdit). Find these
sections and edit directly:

- **Hero headline** — search for "Thoughtful design"
- **Stats strip** — search for "800K+" to find the four metrics
- **Project descriptions** — search for "Coastal Living Room" for the first project
- **About section** — search for "A designer built on listening"
- **Services section** — search for "In-Home Consultations"
- **Contact info** — search for "CallieWells17@gmail.com"

## How to deploy (pick ONE option)

### Option A: Netlify Drop (EASIEST — 2 minutes, free, no account needed for trial)

1. Go to https://app.netlify.com/drop
2. Drag the entire `portfolio-site` folder onto the page
3. Wait 30 seconds — you get a free URL like `amazing-curie-12345.netlify.app`
4. Sign up for free account to customize the URL to `calliewells.netlify.app`

### Option B: GitHub Pages (5 minutes, requires GitHub account)

1. Create a new repo on GitHub called `calliewells.github.io`
2. Upload all files from `portfolio-site` folder
3. Go to Settings → Pages → enable from main branch
4. Wait 2 minutes → your site is live at `https://calliewells.github.io`

### Option C: Custom domain (after you deploy)

1. Buy `calliewells.design` or `calliewellsdesign.com` from Namecheap (~$12/year)
2. In Netlify or GitHub Pages, add the custom domain
3. Follow their DNS instructions (5 minutes)
4. Your site is now at a professional domain for resume/LinkedIn

## What to put on your resume / LinkedIn

Once deployed, add this line to the top of your resume:

> **Portfolio:** calliewells.netlify.app (or your custom domain)

And to the LinkedIn "Featured" section:
- Pin the portfolio URL as a featured link with the title:
  "Portfolio: Residential Design Work"

## Maintaining the site

Monthly: Add 1-2 new project photos, update the stats if numbers grow.
After each project: Consider adding a testimonial to the site with client permission.

## Accessibility + SEO

Already built in:
- Semantic HTML5 structure
- Alt text on all images (update per photo)
- Proper meta description for Google results
- Google Fonts for professional typography (loads ~600KB — acceptable)
- Tailwind CSS via CDN (no build step, loads ~300KB)
- Mobile-responsive out of the box

## Future improvements (optional)

- Add a blog section (shows writing ability)
- Add a "Process" page explaining how a consultation works
- Add client testimonials (with permission)
- Add downloadable resume button
- Add Instagram feed embed if she starts a design IG account
