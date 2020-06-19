# Run "pip3 install qrcode[pil] requests pyyaml python-dateutil" to install dependencies

import datetime
from dateutil import parser
from PIL import Image
import io
import json
import numpy
import os
import qrcode
import requests
import sys
import yaml

# No py 2
if(sys.version_info.major != 3):
	print("This is Python %d!\nPlease use Python 3!" % sys.version_info.major)
	exit()

# Convert names to lowercase alphanumeric + underscore and hyphen
def webName(name):
	name = name.lower()
	out = ""
	for letter in name:
		if letter in "abcdefghijklmnopqrstuvwxyz0123456789-_.":
			out += letter
		elif letter == " ":
			out += "-"
	return out

def downloadScript(file, url):
	if file[file.find(".") + 1:] == "3dsx":
		return [
			{
				"type": "downloadFile",
				"file": url,
				"output": "sdmc:/3ds/" + file,
				"message": "Downloading " + file + "..."
			}
		]
	elif file[file.find(".") + 1:] == "cia":
		return [
			{
				"type": "downloadFile",
				"file": url,
				"output": "sdmc:/" + file,
				"message": "Downloading " + file + "..."
			},
			{
				"type": "installCia",
				"file": "/" + file,
				"message": "Installing " + file + "..."
			},
			{
				"type": "deleteFile",
				"file": "sdmc:/" + file,
				"message": "Deleting " + file + "."
			}
		]
	else:
		return [
			{
				"type": "downloadFile",
				"file": url,
				"output": "sdmc:/" + file,
				"message": "Downloading " + file + "..."
			}
		]

# Read json
with open("source.json", "r") as file:
	source = json.load(file)

# Create UniStore base
unistore = {
	"storeInfo": {
		"title": "Universal-DB",
		"author": "Universal-Team",
		"url": "https://github.com/Universal-Team/db/raw/master/unistore/universal-db.unistore",
		"file": "sdmc:/3ds/Universal-Updater/stores/Universal-DB.unistore",
		"sheet": "sdmc:/3ds/Universal-Updater/stores/Universal-DB.t3x",
		"sheetURL": "https://github.com/Universal-Team/db/raw/master/unistore/universal-db.t3x",
		"description": "Universal DB - An online database of 3DS and DS homebrew",
		"barLight": "#395472",
		"barDark": "#395472",
		"bgDark": "#262c4d",
		"bgLight": "#60a8c0",
		"textDark": "#ffffff",
		"textLight": "#000000",
		"boxDark": "#313131",
		"boxLight": "#f7f7f7",
		"outlineDark": "#000096",
		"outlineLight": "#0000ff",
		"version": 1
	},
	"storeContent": [],
}

# Icons array
icons = []

# Fetch info for GitHub apps and output
for i, app in enumerate(source):
	if "github" in app:
		print("GitHub")
		api = json.loads(requests.get("https://api.github.com/repos/" + app["github"]).content)
		releases = json.loads(requests.get("https://api.github.com/repos/" + app["github"] + "/releases").content)
		release = None
		prerelease = None
		if len(releases) > 0 and releases[0]["prerelease"]:
			prerelease = releases[0]
		for r in releases:
			if not r["prerelease"]:
				release = r
				break

		if not "title" in app:
			app["title"] = api["name"]

		if not "author" in app:
			app["author"] = api["owner"]["login"]

		if not "description" in app and api["description"] != "":
			app["description"] = api["description"]

		if not "image" in app:
			app["image"] = api["owner"]["avatar_url"]
		
		if not "source" in app:
			app["source"] = api["html_url"]
		
		if not "created" in app:
			app["created"] = api["created_at"]

		if not "website" in app and api["homepage"] != "":
			app["website"] = api["homepage"]

		if not "wiki" in app and api["has_wiki"]:
			app["wiki"] = api["html_url"] + "/wiki"

		if release:
			if not "download_page" in app:
				app["download_page"] = release["html_url"]

			if not "version" in app:
				app["version"] = release["tag_name"]

			if not "version_title" in app and release["name"] != None:
				app["version_title"] = release["name"]

			if not "updated" in app:
				app["updated"] = release["published_at"]

			if not "downloads" in app:
				app["downloads"] = {}
			for asset in release["assets"]:
				if not asset["name"] in app["downloads"]:
					app["downloads"][asset["name"]] = asset["browser_download_url"]
		
		if prerelease:
			if not "prerelease" in app:
				app["prerelease"] = {}

			if not "download_page" in app["prerelease"]:
				app["prerelease"]["download_page"] = prerelease["html_url"]

			if not "version" in app["prerelease"]:
				app["prerelease"]["version"] = prerelease["tag_name"]

			if not "version_name" in app["prerelease"] and prerelease["name"] != None:
				app["prerelease"]["version_name"] = prerelease["name"]

			if not "updated" in app["prerelease"]:
				app["prerelease"]["updated"] = prerelease["published_at"]

			if not "downloads" in app["prerelease"]:
				app["prerelease"]["downloads"] = {}
			for asset in prerelease["assets"]:
				if not asset["name"] in app["prerelease"]["downloads"]:
					app["prerelease"]["downloads"][asset["name"]] = asset["browser_download_url"]

	print("=" * 80)
	if "title" in app:
		print(webName(app["title"]))

	# Output website page
	if "downloads" in app:
		for item in app["downloads"]:
			if item[item.find(".") + 1:] == "cia":
				qrcode.make(app["downloads"][item]).save(os.path.join("..", "assets", "images", "qr", webName(item) + ".png"))
				if not "qr" in app:
					app["qr"] = {}
				app["qr"][item] = "https://universal-team.github.io/db/assets/images/qr/" + webName(item) + ".png"
	web = app.copy()
	web["layout"] = "app"
	if "long_description" in web:
		web.pop("long_description")
	if not "title" in web:
		web["title"] = str(i)
	if not "system" in web:
		web["system"] = "3DS" # default to 3DS
	with open(os.path.join("..", "_" + webName(web["system"]), webName(web["title"]) + ".md"), "w") as file:
		file.write("---\n" + yaml.dump(web) + "---\n")
		if "long_description" in app:
			file.write(app["long_description"])

	# Create copy with filler items for UniStore base
	appCopy = app.copy()
	if not "title" in app:
		appCopy["title"] = ""
	if not "version" in app:
		appCopy["version"] = ""
	if not "author" in app:
		appCopy["author"] = ""
	if not "categories" in app:
		appCopy["categories"] = [""]
	if not "system" in app:
		appCopy["system"] = ""
	if not "description" in app:
		appCopy["description"] = ""

	if "icon" in app or "image" in app:
		if not os.path.exists("temp"):
			os.mkdir("temp")

		if "icon" in app:
			r = requests.get(app["icon"])
		else:
			r = requests.get(app["image"])

		with Image.open(io.BytesIO(r.content)) as img:
			if img.mode == "P":
				pal = img.palette.getdata()[1]
				img = img.convert("RGBA")
				data = numpy.array(img)
				r, g, b, a = data.T
				transparent = (r == pal[2]) & (g == pal[1]) & (b == pal[0])
				data[...][transparent.T] = (0, 0, 0, 0)
				img = Image.fromarray(data)
			img.thumbnail((48, 48))
			img.save(os.path.join("temp", str(i) + ".png"))
			icons.append(str(i) + ".png")

	# Add entry for UniStore
	uni = {
		"info": {
			"title": appCopy["title"],
			"version": appCopy["version"],
			"author": appCopy["author"],
			"category": appCopy["categories"][0],
			"console": appCopy["system"],
			"icon_index": i,
			"description": appCopy["description"],
		}
	}
	if "updated" in app:
		uni["info"]["last_updated"] = parser.parse(app["updated"]).strftime("%Y-%m-%d at %H:%M (UTC)")

	if "downloads" in app:
		for file in app["downloads"]:
			uni["Download " + file] = downloadScript(file, app["downloads"][file])

	if "prerelease" in app:
		for file in app["prerelease"]["downloads"]:
			uni["Download " + file + " (prerelease)"] = downloadScript(file, app["prerelease"]["downloads"][file])

	unistore["storeContent"].append(uni)

# Make t3x
with open(os.path.join("temp", "icons.t3s"), "w") as file:
	file.write("--atlas -f rgba -z auto\n\n")
	for icon in icons:
		file.write(icon + "\n")
os.system("tex3ds -i " + os.path.join("temp", "icons.t3s") + " -o " + os.path.join("..", "unistore", "universal-db.t3x"))

# Write unistore to file
with open(os.path.join("..", "unistore", "universal-db.unistore"), "w") as file:
	file.write(json.dumps(unistore))
