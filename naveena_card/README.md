# The Tilak Card: Naveena Neerada Dasa

A one-page digital business card. Everything that gets published is in the `site/` folder.

```
photo.jpg          original portrait (never modified; copy of "Naveena Neerada Dasa.jpg")
build-vcf.py       builds the contact file, the QR code and the web portrait
render-images.py   builds the favicons and the link-preview image (og-image.jpg)
tools/og.html      design template for og-image.jpg
netlify.toml       tells Netlify to publish site/
site/              the website (this is what you deploy)
```

## Changing your details

1. Open `build-vcf.py` and edit the `CONTACT` block at the top (phone, email, address, etc.).
2. Run it:

   ```
   pip install pillow segno
   python build-vcf.py
   ```

   This regenerates:
   - `site/naveena-neerada-dasa.vcf`: the "Save My Contact" file, with your photo embedded
   - `site/qr-contact.svg`: the QR code (contact only, no photo, so it works offline)
   - `site/img/naveena.webp` and `naveena.jpg` (photo.jpg cropped to the card's 300x385 frame; adjust `PORTRAIT_CROP` in `build-vcf.py` if you swap the photo)

3. The text shown on the page lives in `site/index.html`. If you changed your phone, email or address, update the matching links there too (search for the old value).
4. To use a new photo, replace `photo.jpg` and run both scripts. A larger, sharper original (800px wide or more) will look crisper on high-resolution phones.
5. If you changed your name, title or photo, also refresh the link-preview image and icons:

   ```
   pip install pillow playwright
   python render-images.py
   ```

   It uses your installed Microsoft Edge or Chrome, so there's nothing extra to download. If you edit the name or title, also update `tools/og.html`.

After any change, deploy again (below). WhatsApp and iMessage cache link previews, so a new preview can take a while to show up.

## Deploying to Netlify

### Option A: drag and drop
1. Log in at https://app.netlify.com.
2. Go to **Sites → Add new site → Deploy manually**.
3. Drag the **`site`** folder (not the whole project folder) onto the page.
4. To update later: open the site → **Deploys** → drag the `site` folder in again.

### Option B: Netlify CLI
```
npm install -g netlify-cli
netlify login
netlify deploy            # draft preview URL
netlify deploy --prod     # publish
```
Run these from the project folder. `netlify.toml` already points Netlify at `site/`. The first run asks you to create or link a site.

### After the first deploy: set your web address
The link-preview tags in `site/index.html` use `https://naveena-dasa.netlify.app/`. If your site gets a different address (or you add a custom domain), replace that address everywhere in `index.html` (canonical, `og:url`, `og:image`, `twitter:image`) and deploy again. The QR code and contact file don't depend on the web address.

Tip: in Netlify, **Site configuration → Change site name** lets you choose `naveena-dasa` so the default address matches.

## How it works
- **Save My Contact** links to the static `naveena-neerada-dasa.vcf` file. `site/_headers` makes Netlify serve it as `text/vcard`. On iPhone the page drops the `download` attribute, so Safari opens the "Create New Contact" sheet directly instead of saving to Downloads. Android downloads the file and offers to add it to Contacts.
- **The QR code** holds the contact itself (vCard 3.0, error correction M), so scanning saves the contact even without internet.
- The page has no frameworks. Its only outside dependency is Google Fonts.
