from prathameshost import app
from flask import request, render_template, redirect, flash, url_for, Response
from google.appengine.api import users
from google.appengine.ext import db
from prathameshost.models import Category, Vote, Comments
import xml.dom.minidom
import cgi,cgitb
import datetime
import random

@app.route('/')
def index():
	x=0
	user1=""
	user1 = users.get_current_user()
	nick = user1.nickname()
	return render_template('homepage.html',user=nick)

@app.route('/option')
def select():
	form = cgi.FieldStorage()
	#create1="Hi"
	vote1="low"
	item1="hello"
	create1 = form.getvalue('startoption')
        if create1=="Create":
		return render_template('CreateCategory.html')
	elif create1=="Item":
		username = users.get_current_user()
		name = username.nickname()
		categories = db.GqlQuery("Select * from Category where username = :1",name)
		return render_template('sample.html',categ=categories,user1=name)	
	elif create1=="result":
		return render_template('resultschoice.html')
	#vote1 = request.form['Vote']
	#item1 = request.form['AddItem']
	else:
		return render_template('voteoptions.html',create=create1,vote=vote1,item=item1)

@app.route('/storenewcategory')
def store():
	#resultset = db.GqlQuery("Select * from Category")
	#db.delete(resultset)
	currentuser = users.get_current_user()
	nickname = currentuser.nickname()
	form = cgi.FieldStorage()
	cnames = form.getvalue("categoryname")
	alreadyexists = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",nickname,cnames)
	if alreadyexists.count()>0:
		return render_template("categoryexists.html")
	else:
		itemnames = form.getvalue("items")
		itemlist = itemnames.split(",")
		newCategory = Category(username=nickname,categoryname=cnames)
		newCategory.items=itemlist
		newCategory.put()
		resultset = db.GqlQuery("Select * from Category")
		return render_template('Successfulnewcateg.html',results=cnames)

@app.route('/voteforcategory')
def vote():
	return render_template('voteoptions.html')

@app.route('/showvotecategs')
def selectvotecategories():
	currentuser = users.get_current_user()
	nickname = currentuser.nickname()
	form = cgi.FieldStorage()
	selection = form.getvalue("owner");
	if selection=="mycategory":
		resultset = db.GqlQuery("Select * from Category where username = :1",nickname)
	else:
		resultset = db.GqlQuery("Select * from Category where username != :1",nickname)
	return render_template('newcateg.html',results=resultset)

@app.route('/viewitemsforvote')
def showitemsforvote():
	itemlist=[]
	form = cgi.FieldStorage()
	selected = form.getvalue("selectedcategory")
	selectedlist = selected.split('/')
	categoryname = selectedlist[0]
	username = selectedlist[1]
	results = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",username,categoryname)
	#result = results.fetch(1)
	cdate = datetime.datetime.now()
	for res in results:
		itemlist = res.items
		cdate = res.expirydate;
	actuallist = []
	flag = "empty"
	if len(itemlist)==1:
		actuallist.append(itemlist[0])
	else:
		choice1=0
		choice2=0
		while choice1==choice2:
			choice1 = random.randint(0,len(itemlist)-1)
			choice2 = random.randint(0,len(itemlist)-1)
		actuallist.append(itemlist[choice1])
		actuallist.append(itemlist[choice2])
	if cdate is None:
		return render_template('viewitemsforvote.html',items=actuallist,user=username,category=categoryname,noofitems=len(actuallist),expired="no")
	elif cdate>=datetime.datetime.now():
		return render_template('viewitemsforvote.html',items=actuallist,user=username,category=categoryname,noofitems=len(actuallist),expired="no")
	else:
		return render_template('viewitemsforvote.html',items=actuallist,user=username,category=categoryname,noofitems=len(actuallist),expired="yes")

@app.route('/voted')
def storevotes():
	form = cgi.FieldStorage()
	button = form.getvalue("submitvote")
	voteitem = form.getvalue("votechoice")
	itemone = form.getvalue("itemone")
	itemtwo = form.getvalue("itemtwo")
	winner = ""
	loser = ""
	if itemone==voteitem:
		winner = itemone
		loser = itemtwo
	else:
		winner = itemtwo
		loser = itemone
	currentuser = users.get_current_user()
	nickname = currentuser.nickname()
	categowner = form.getvalue("categoryowner")
	categname = form.getvalue("categoryname")
	if button=="Vote":
		message = "" 
		resultset = db.GqlQuery("Select * from Vote where username = :1 and categoryname = :2 and itemname = :3",categowner,categname,winner)
		if resultset.count()==0:
			newvote = Vote(username=categowner,categoryname=categname,itemname=winner)
			newvote.wins=1
			newvote.loss=0
			newwins = 1;
			newvote.put()
		else:
			newwins = 0
			oldloss = 0
			for result in resultset:
				oldloss = result.loss
				newwins = result.wins + 1
			db.delete(resultset)
			newvote = Vote(username=categowner,categoryname=categname,itemname=winner)
			newvote.wins = newwins
			newvote.loss = oldloss
			newvote.put()
		loserresultset = db.GqlQuery("Select * from Vote where username = :1 and categoryname = :2 and itemname = :3",categowner,categname,loser)
		if loserresultset.count()==0:
			newloss = Vote(username=categowner,categoryname=categname,itemname=loser)
			newloss.wins=0
			newloss.loss=1
			losses=1
			newloss.put()
		else:
			losses=0
			oldwins=0
			for lresult in loserresultset:
				oldwins = lresult.wins
				losses = lresult.loss + 1
			db.delete(loserresultset)
			newloss = Vote(username=categowner,categoryname=categname,itemname=loser)
			newloss.wins= oldwins
			newloss.loss = losses
			newloss.put()
		return render_template('results.html',wins=newwins,lossesn=losses,categ=categname,winitem=winner,lossitem=loser,fmessage=message)
	else:	
		return render_template('postcomments.html',user1=nickname,owner=categowner,categ=categname,item=voteitem)

@app.route('/viewResults')
def results():
	form = cgi.FieldStorage()
	currentuser = users.get_current_user()
	nickname = currentuser.nickname()
	categ = form.getvalue("resultCategory")
	user = form.getvalue("resultUsername")
	resultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
	count = resultset.count()
	itemlist = []
	for result in resultset:
		itemlist = result.items
	wins=[]
	noofwins = 0
	noofloss = 0
	itemcomment=""
	for item in itemlist:
		itemcomment = ""
		commentrows = db.GqlQuery("Select * from Comments where owner = :1 and categoryname = :2 and itemname = :3",user,categ,item)
		if commentrows.count()==0:
			itemcomment="No comments"
		else:
			for exp in commentrows:
				itemcomment= itemcomment + "###" + exp.username + "|||" + exp.comment	
		tuples = db.GqlQuery("Select * from Vote where username = :1 and categoryname = :2 and itemname = :3",user,categ,item)
		if tuples.count() != 0:
			for tpl in tuples:
				noofwins = tpl.wins
				noofloss = tpl.loss
			wins.append(item + ":" +  str(noofwins) + ":" + str(noofloss) + ":" + itemcomment)
		else:
			wins.append(item + ":" + str(0) + ":" + str(0) + ":" + itemcomment)
	
	return render_template("displayresults.html",winlist=wins,category=categ,count1=count,us=user,ct=categ,length1=len(wins))		
		
@app.route('/editcateg')
def editcateghome():
	form = cgi.FieldStorage()
	user = form.getvalue("categuser")
	selectedcateg = form.getvalue("changecategory")
	results = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,selectedcateg)
	listitems = []
	for result in results:
		listitems = result.items
	return render_template("listeditcategs.html",user1=user,categ=selectedcateg,itemlist=listitems)

@app.route('/submitchangecateg')
def addnewitems():
	form = cgi.FieldStorage()
	user = form.getvalue("categowner")
	categ = form.getvalue("categchange")
	newitems = form.getvalue("addeditems")
	newitemlist = newitems.split(",")
	oldresultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
	olditemlist = []
	rejecteditems = []
	for result in oldresultset:
		olditemlist = result.items
	for item in newitemlist	:
		if item in olditemlist:
			rejecteditems.append(item)
		else:
			olditemlist.append(item)
	db.delete(oldresultset)
	newcategory = Category(username=user,categoryname=categ)
	newcategory.items = olditemlist
	newcategory.put()
	newresultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
	for result in newresultset:
		finalresult = result
	return render_template('changedcategory.html',user1=user,category=categ,old=olditemlist,rej=rejecteditems,fresult=finalresult)
		
@app.route('/deleteitems')
def deleteedititems():
	form = cgi.FieldStorage()
	itemstobedeleted = form.getvalue("deleteitemnames")
	user = form.getvalue("deleteuser")
	categ = form.getvalue("deletecateg")
	oldresultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
	olditems = []
	for result in oldresultset:
		olditems = result.items
	newlistitems = []
	rejectitems = []
	for item in olditems:
		if item in itemstobedeleted:
			rejectitems.append(item)
		else:
			newlistitems.append(item)
	deleteset = db.GqlQuery("Select * from Vote where username = :1 and categoryname = :2 and itemname in :3",user,categ,rejectitems)
	db.delete(deleteset)
	db.delete(oldresultset)
	newcategoryadd = Category(username=user,categoryname=categ)
	newcategoryadd.items = newlistitems
	newcategoryadd.put()
	newresult = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
	newitems = []
	for result in newresult:
		newitems = result.items
	return render_template("deleteditems.html",user1=user,category=categ,newitemlist=newitems)
	
@app.route('/storecomments')
def savecomments():
	user = users.get_current_user()
	nickname = user.nickname()
	form = cgi.FieldStorage()
	owner1 = form.getvalue("owner")
	categ = form.getvalue("cname")
	itemname1 = form.getvalue("itemname")
	comments = form.getvalue("thecomment")
	response=""
	resultset = db.GqlQuery("Select * from Comments where owner = :1 and username = :2 and categoryname = :3 and itemname = :4",owner1,nickname,categ,itemname1)
	if resultset.count()==0:
		newcomment = Comments(owner=owner1,username=nickname,categoryname=categ,itemname=itemname1)
		newcomment.comment = comments
		newcomment.put()
		response = "Your comment has been successfully stored"
	else:
		response = "You have already commented on this item before. you are not allowed to comment on the same item again. Thank you"
	return render_template("commentresponse.html",status=response,item=itemname1)

@app.route('/createxml')
def uploadxml():
	currentuser = users.get_current_user()
	nickname = currentuser.nickname()
	form = cgi.FieldStorage()
	#xmlfile = form["filename"]
	#data = "No data entered"
	fileitem = form['filename']

	# Test if the file was uploaded
	if fileitem.filename:
  		# strip leading path from file name to avoid 
  		# directory traversal attacks
   		fn = os.path.basename(fileitem.filename)
   		open('/tmp/' + fn, 'wb').write(fileitem.file.read())
   		message = 'The file "' + fn + '" was uploaded successfully'
   
	else:
   		message = 'No file was uploaded'
	message1=""
	xmldata = "<CATEGORY><NAME>Soccer Players</NAME><ITEM><NAME>Santi Cazorla</NAME></ITEM><ITEM><NAME>Robin Van Persie</NAME></ITEM><ITEM><NAME>Cesc Fabregas</NAME></ITEM><ITEM><NAME>Thierry Henry</NAME></ITEM></CATEGORY>"
	dom = parseString(xmldata)
	xmlTag = dom.getElementsByTagName('CATEGORY')
	if len(xmlTag)==0:
		message1 = "Category element not specified in Xml. Incorrect format"
		return render_template('xmlresult.html',fmessage=message1)
	#strip off the tag (<tag>data</tag>  --->   data):
	categNameElements = dom.getElementsByTagName('NAME')
	if len(categNameElements)==0:
		message1 = "Category name element not specified in the XML. Incorrect Format"
		return render_template('xmlresult.html',fmessage=message1)
	categNameEle = dom.getElementsByTagName('NAME')[0].toxml()
	categName = categNameEle.replace('<NAME>','').replace('</NAME>','')
	itemElements = dom.getElementsByTagName('ITEM')
	listitems=[]
	for itemElement in itemElements:
		itemE = itemElement.toxml()
		itemtag = itemE.replace('<ITEM>','').replace('</ITEM>','')
		itemname = itemtag.replace('<NAME>','').replace('</NAME>','')
		listitems.append(itemname)
	resultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",nickname,categName)
	if resultset.count()==0:
		newcategory=Category(username=nickname,categoryname=categName)
		newcategory.items = listitems
		newcategory.put()
		message1 = categName + " category created successfully"
		return render_template("xmlresult.html",fmessage=message1)
	else:
		message1 = "Category already exists"
		return render_template("xmlresult.html",fmessage=message1)
	#if xmlfile.file:
	#data = xmlfile.file.read()
	#dom1 = parseString(data)
	#xmltag = dom.getElementsByTagName('CATEGORY')
	#return render_template("newcategxml.html",upfile=message,dataxml=categName,tagxml=xmlTag,items=listitems)			

@app.route('/exportxml')
def exportxmlfile():
	form = cgi.FieldStorage()
	categname = form.getvalue("xmlCategory")
	owner = form.getvalue("xmlowner")
	resultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",owner,categname)
	itemlist = []
	for result in resultset:
		itemlist = result.items
	xmlfile = "<CATEGORY>"
	xmlfile = xmlfile + "<NAME>" + categname + "</NAME>"
	for item in itemlist:
		xmlfile = xmlfile + "<ITEM><NAME>" + item + "</NAME></ITEM>"
	xmlfile = xmlfile + "</CATEGORY>"
	return render_template("xmlexported.html",xmlop=xmlfile)

@app.route('/deletecategperm')
def deletecategfromlist():
	form = cgi.FieldStorage()
	userd = form.getvalue("deleteusername")
	categd = form.getvalue("deletecategname")
	resultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",userd,categd)
	db.delete(resultset)
	voteset = db.GqlQuery("Select * from Vote where username = :1 and categoryname = :2",userd,categd)
	db.delete(voteset)
	commentset = db.GqlQuery("Select * from Comments where owner = :1 and categoryname = :2",userd,categd)
	db.delete(commentset)
	message = "Category deleted successfully"
	return render_template("categorydelete.html",fmessage=message)

@app.route('/changecategoryname')
def newcategoryname():
	itemlist=[]
	form = cgi.FieldStorage()
	newcname = form.getvalue("newcategname")
	user = form.getvalue("changeusername")
	categ = form.getvalue("changecategname")
	wrongname = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,newcname)
	message = ""
	if wrongname.count()!=0:
		message = "This category name already exists. Please enter another categoryname"
	else:
		rightname = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
		voteresults = db.GqlQuery("Select * from Vote where username = :1 and categoryname = :2",user,categ)
		olditemname=""
		oldusername=""
		oldwins=0
		oldloss=0
		for vote in voteresults:
			olditemname=vote.itemname
			oldusername=vote.username
			oldwins=vote.wins
			oldloss=vote.loss
			newvote=Vote(username=oldusername,categoryname=newcname,itemname=olditemname)
			newvote.wins=oldwins
			newvote.loss=oldloss
			newvote.put()
		db.delete(voteresults)
		commentresults = db.GqlQuery("Select * from Comments where owner = :1 and categoryname = :2",user,categ)
		oldowner=""
		oldusername=""
		oldcomment=""
		olditemname=""
		for comments in commentresults:
			oldowner = comments.owner
			oldusername = comments.username
			olditemname = comments.itemname
			oldcomment = comments.comment
			newcomment = Comments(owner=oldowner,username=oldusername,categoryname=newcname,itemname=olditemname)
			newcomment.comment = oldcomment
			newcomment.put()
	        db.delete(commentresults)		
		for result in rightname:
			itemlist = result.items	
		newnamecateg = Category(username=user,categoryname=newcname)
		newnamecateg.items = itemlist
		db.delete(rightname)
		newnamecateg.put()
		message="Category name has been successfully updated to " + newcname
	return render_template("categorynameresult.html",output=message)

@app.route('/modifydate')
def moddate():
	form = cgi.FieldStorage()
	month = form.getvalue("Month")
	day = form.getvalue("day")
	year = form.getvalue("year")
	hour = form.getvalue("hour")
	minutes = form.getvalue("min")
	#ampm = form.getvalue("ampm")
	user = form.getvalue("dateuser")
	categ = form.getvalue("datecateg")
	hour1=int(hour)
	#if str(ampm)=="pm":
	#	hour1 = int(str(hour))
	#	hour1 = hour1 + 12
	day1 = int(str(day))
	year1 = int(str(year))
	month1 = int(str(month))
	minutes1 = int(str(minutes))
	date = datetime.datetime(year1,month1,day1,hour1,minutes1)
	resultset = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
	itemlists = []
	for result in resultset:
		itemlists = result.items
	newCategory=Category(username=user,categoryname=categ)
	newCategory.items = itemlists
	newCategory.expirydate = date
	db.delete(resultset)
	newCategory.put()
	newdate = datetime.datetime(2012,4,3,10,12)
	dateresult = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",user,categ)
	for result in dateresult:
		newdate = result.expirydate
	return render_template("moddate.html",dateobj=newdate)

@app.route('/uploadxml',methods=['GET','POST'])
def uploadXMLFile():
	form = cgi.FieldStorage();
	item = form["filename"];
	data = "";
	if item.file:
		data = item.file;
	try:
		doc = xml.dom.minidom.parse(data)
	except:
		message="Malformed XML Input"
		return render_template("xmlerror.html",error=message)
	items = doc.getElementsByTagName("NAME");
	itemtag = doc.getElementsByTagName("ITEM");
	if len(items) <= 1 or len(itemtag)!=len(items)-1:
		message="Category item missing or no items included in the XML"
		return render_template("xmlerror.html")
	owner = users.get_current_user().nickname()
	optionList = [];
	for node in items:
		optionList.append(node.firstChild.nodeValue);
	categoryName = optionList[0];
	existingcateg = db.GqlQuery("Select * from Category where username = :1 and categoryname = :2",owner,categoryName)
	if existingcateg.count()==0:
		optionList.remove(categoryName);
		newCategory = Category(username=owner,categoryname=categoryName);
		newCategory.items = optionList
		newCategory.put();
		return render_template('newxmlcateg.html',categ=categoryName,option=optionList);
	else:
		exitemset=[]
		rejitemset=[]
		for result in existingcateg:
			exitemset = result.items
		optionList.remove(categoryName)
		for item in exitemset:
			if item not in optionList:
				rejitemset.append(item)
		for item in rejitemset:
			deletedvotes = db.GqlQuery("Select * from Vote where username = :1 and categoryname = :2 and itemname = :3",owner,categoryName,item)
			db.delete(deletedvotes)
			deletecomments = db.GqlQuery("Select * from Comments where username = :1 and categoryname = :2 and itemname = :3",owner,categoryName,item)
			db.delete(deletecomments)
		editedcateg = Category(username=owner,categoryname=categoryName)
		editedcateg.items = optionList
		db.delete(existingcateg)
		editedcateg.put()
		return render_template("xmleditcateg.html",categname=categoryName,newlist=optionList,deletelist=rejitemset)



@app.route('/download')
def download():
	form = cgi.FieldStorage();
	categ = form.getvalue("xmlCategory")
        user = form.getvalue("xmlowner")
	resultset = db.GqlQuery("SELECT * FROM Category WHERE username = :1 and categoryname = :2",user,categ);
	itemList = [];
	for result in resultset:
		itemList = result.items;
	def generate():
		textdata = "<CATEGORY>" + "\n" + "<NAME>" + categ +"</NAME>" + "\n";
		yield textdata;
		for item in itemList:
			text = "<ITEM>"+ "\n" + "<NAME>" + item + "</NAME>" + "\n" + "</ITEM>" + "\n";
			yield text;
		yield "</CATEGORY>";
	return Response(generate(), mimetype='text/csv');	

