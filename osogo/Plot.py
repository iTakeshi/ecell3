#!/usr/bin/env python

import gtk 
from Numeric import *
import gtk.gdk
import gobject
import re
from string import *
from math import *
import operator

from ecell.ecssupport import *

#class Plot,
 
#initializes graphics
#changes screen, handles color allocation when adding/removing traces
#clears plot areas on request, sets tityle


class Plot:


	def __init__( self, owner, scale_type, root, width, heigth ):
	# ------------------------------------------------------
	    self.scale_type=scale_type
	    self.ColorFullPNMap={"pen":"black", "background":"grey"} # key is FullPN, value color
	    self.GCFullPNMap={} 
	    self.ColorList=["pink","cyan","yellow","navy",
			    "brown","white","purple","black",
			    "green", "orange","blue","red"]
	    self.mes_dict = \
		[['System', 'Size' , '??'],
		['Variable', 'MolarConc', 'mol/l' ],
		['Variable', 'NumberConc', '1/l' ],
		['Variable', 'TotalVelocity', '??' ],
		['Variable', 'Value', 'no. of molecules'],
		['Variable', 'Velocity', '??' ],
		['Process', 'Activity', '??'  ]]

	    self.xmes=''
	    self.ymes=''

	    self.data_list=[] #list of displayed fullpnstrings
	    self.trace_onoff={}
	    self.available_colors=[]
	    for acolor in self.ColorList:
		self.available_colors.append(acolor)
	    self.GUI_Button_Shown = False

	    self.pixmapmap={} #key is color, value pixmap
	    self.FullPNMap={} #key: FullPNString, values [FullPN,shortname]
	    self.plotwidth=width
	    self.plotheigth=heigth

	    self.xframe=[]
	    self.yframe=[]
	    #creates widget
	    self.theWidget=gtk.DrawingArea()
	    self.theWidget.set_size_request(self.plotwidth,self.plotheigth)
	    #add buttonmasks to widget
	    self.theWidget.set_events(gtk.gdk.EXPOSURE_MASK|gtk.gdk.BUTTON_PRESS_MASK|
					gtk.gdk.LEAVE_NOTIFY_MASK|gtk.gdk.POINTER_MOTION_MASK|
					gtk.gdk.BUTTON_RELEASE_MASK)
	
	    root = root[root.__class__.__name__]
	    self.theRoot=root
	    self.theColorMap=self.theWidget.get_colormap()
	    newgc=root.window.new_gc()
	    newgc.set_foreground(self.theColorMap.alloc_color(self.ColorFullPNMap["pen"]))
	    self.GCFullPNMap["pen"]=newgc
	    newgc=root.window.new_gc()
	    newgc.set_foreground(self.theColorMap.alloc_color(self.ColorFullPNMap["background"]))
	    self.GCFullPNMap["background"]=newgc
	    self.st=self.theWidget.get_style()
	    self.font=gtk.gdk.font_from_description(self.st.font_desc)
	    self.ascent=self.font.ascent
	    self.descent=self.font.descent
	    self.pm=gtk.gdk.Pixmap(root.window,self.plotwidth,self.plotheigth,-1)
	    self.pm2=gtk.gdk.Pixmap(root.window,self.plotwidth,self.plotheigth,-1)
	    newpm=gtk.gdk.Pixmap(root.window,10,10,-1)
	    newgc=root.window.new_gc()
	    for acolor in self.ColorList:
		newgc.set_foreground(self.theColorMap.alloc_color(acolor))
		newpm.draw_rectangle(newgc,gtk.TRUE,0,0,10,10)
		pb=gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,gtk.TRUE,8,10,10)
		newpb=pb.get_from_drawable(newpm,self.theColorMap,0,0,0,0,10,10)
		self.pixmapmap[acolor]=newpb
	    self.recalculate_size()	    
	    self.zoomlevel=0
	    self.zoombuffer=[]
	    self.zoomkeypressed=False
	    self.button_timestamp=None
	    self.theOwner=owner
	    #initializes variables
	    self.xframe_when_rescaling=0.5
	    self.yvaluemax_trigger_rescale=0.70 #if max(values) falls to low
	    self.yvaluemin_trigger_rescale=0.30
	    self.yframemin_when_rescaling=0.1
	    self.yframemax_when_rescaling=0.9	    
	    self.stripinterval=1000
	    self.zerovalue=1e-50 #very small amount to substitute 0 in log scale calculations
	    # stripinterval/pixel
	    self.requires_scale=gtk.TRUE
	    self.size_status='maximized'
	    #initialize data buffers
	    self.data_stack={} #key:FullPNString, value: DataBuffer[[x0,y0],[x1,y1],[x2,y2]]}	
	    self.lastx={}
	    self.lasty={}
	    self.strip_mode='strip'
	    self.zoomlevel=0    
	    #set yframes
	    self.yframe=[0,1]
	    self.ygrid=[0,1]
	    self.xframe=[0.0,1000]
	    self.xgrid=[0,1000]
	    self.clearplot()
	    self.drawaxes()
	    self.reframey()
	    self.reframex()
	    self.drawall()
	    self.definemeasures()
	    self.theWidget.connect('expose-event',self.expose)
	    self.theWidget.connect('button-press-event',self.press)
	    self.theWidget.connect('motion-notify-event',self.motion)
	    self.theWidget.connect('button-release-event',self.release)


	def recalculate_size(self):
	    self.max_yticks_no=int(self.plotheigth/150)*5
	    self.max_xticks_no=int(self.plotwidth/100)
	    self.origo=[70,self.plotheigth-30]
	    self.plotarea=[self.origo[0],30,\
	    	self.plotwidth-60-self.origo[0],\
	    	self.origo[1]-30]
	    self.plotaread=[self.plotarea[0],self.plotarea[1],\
	    	self.plotarea[2]+self.plotarea[0],\
	    	self.plotarea[3]+self.plotarea[1]]
	    self.ylabelsarea=[0,0,self.origo[0]-1,self.origo[1]+5]
	    self.xlabelsarea=[0,self.origo[1]+5,\
	    	self.plotwidth,25]
	    self.xticksarea=[self.origo[0],self.origo[1]+2,\
	    	self.plotwidth-self.origo[0],3]
	    self.yaxis_x=self.origo[0]-1
	    self.xaxis_y=self.origo[1]+1
	    self.xaxislength=self.plotarea[2]+1
	    self.yaxislength=self.plotarea[3]+1
	    self.gui_button_area = [self.plotwidth-20, 0, 20, 20 ]
	    self.xmes_ltop=[self.plotaread[2]+10,self.origo[1]-10]

	    self.ymes_ltop=[self.origo[0]-50, 0]


	def show_gui_button( self ):
		self.GUI_Button_Shown = True

		self.draw_gui_button()


	def hide_gui_button( self ):
		self.GUI_Button_Shown = False
		self.draw_gui_button()


	def draw_gui_button (self ):
		if self.GUI_Button_Shown:
			rct=self.gui_button_area
			self.drawline("pen", rct[0], rct[1], rct[0]+rct[2],rct[1] )
			self.drawline("pen", rct[0], rct[3]+rct[1], rct[0]+rct[2],rct[3]+rct[1] )
			self.drawline("pen", rct[0], rct[1], rct[0], rct[3]+rct[1] )
			self.drawline("pen", rct[2]+rct[0], rct[1], rct[0]+rct[2], rct[3]+rct[1] )

			self.drawline("pen", rct[0]+4, rct[1]+4, rct[0]+16,rct[1]+4 )
			self.drawline("pen", rct[0]+4, rct[1]+5, rct[0]+16,rct[1]+5 )
			self.drawline("pen", rct[0]+4, rct[1]+6, rct[0]+16,rct[1]+6 )
			self.drawline("pen", rct[0]+4, rct[1]+4, rct[0]+4,rct[1]+16 )
			self.drawline("pen", rct[0]+16, rct[1]+4, rct[0]+16,rct[1]+16 )
			self.drawline("pen", rct[0]+4, rct[1]+16, rct[0]+16,rct[1]+16 )


		else:
			self.drawbox("background", self.gui_button_area[0], self.gui_button_area[1], \
				self.gui_button_area[2], self.gui_button_area[3]+1 )


	def expose(self, obj, event):
	    obj.window.draw_drawable(self.pm.new_gc(),self.pm,event.area[0],event.area[1],
					event.area[0],event.area[1],event.area[2],event.area[3])


	def allocate_color(self, aFullPNString):		
	    #checks whether there's room for new traces
	    if len(self.available_colors)>0 and \
		(not self.data_list.__contains__(aFullPNString)):
		#allocates a color
		allocated_color=self.available_colors.pop()
		self.data_list.append(aFullPNString)
		self.trace_onoff[aFullPNString]=gtk.TRUE
		return self.register_color(aFullPNString,allocated_color)
	    else:
		return None
	
	def register_color(self,fpn,color):
	    	self.ColorFullPNMap[fpn]=color
		newgc=self.pm.new_gc()
		newgc.set_foreground(self.theColorMap.alloc_color(color))
		self.GCFullPNMap[fpn]=newgc
		return self.pixmapmap[color]

	def remove_color(self, FullPNStringList):
	    #remove from colorlist
	    for fpn in FullPNStringList:
		self.deregister_color(fpn)
		self.ColorFullPNMap.__delitem__(fpn)
		self.GCFullPNMap.__delitem__(fpn)

	def deregister_color(self, fpn):
	    acolor=self.ColorFullPNMap[fpn]
	    if not self.available_colors.__contains__(acolor):
		self.available_colors.append(acolor)
	    
	    
	def clearplotarea(self):
	    self.drawbox("background",self.plotarea[0],self.plotarea[1],self.plotarea[2]+1,
			self.plotarea[3]+1)

	def clearplot(self):
	    self.drawbox("background",0,0,self.plotwidth,self.plotheigth)
	    
	def clearxlabelarea(self):
	    self.drawbox("background",self.xlabelsarea[0],self.xlabelsarea[1],
			self.xlabelsarea[2],self.xlabelsarea[3])
	    self.drawbox("background",self.xticksarea[0],self.xticksarea[1],
			self.xticksarea[2],self.xticksarea[3])
	    
	def clearylabelarea(self):
	    self.drawbox("background",self.ylabelsarea[0],self.ylabelsarea[1],
			self.ylabelsarea[2],self.ylabelsarea[3])

	def drawaxes(self):
		self.drawxaxis()
		self.drawyaxis()
	
	def drawxaxis(self):
	    self.drawline("pen", self.yaxis_x,self.xaxis_y,
			    self.yaxis_x+self.xaxislength,self.xaxis_y)
	    
	def drawyaxis(self):
	    self.drawline("pen", self.yaxis_x,self.xaxis_y-self.yaxislength,
			    self.yaxis_x,self.xaxis_y)
	    
	def drawpoint_on_plot(self, aFullPNString,x,y):
	    #uses raw plot coordinates!
	    self.pm.draw_point(self.GCFullPNMap[aFullPNString],x,y)
	    self.theWidget.queue_draw_area(x,y,1,1)
    	
	    
	def drawline(self, aFullPNString,x0,y0,x1,y1):
	    #uses raw plot coordinates!	    
	    self.pm.draw_line(self.GCFullPNMap[aFullPNString],x0,y0,x1,y1)
	    self.theWidget.queue_draw_area(min(x0,x1),min(y0,y1),abs(x1-x0)+1,\
	    abs(y1-y0)+1)
	    return [x1,y1]

	def drawbox(self, aFullPNString,x0,y0,width,heigth):
	    #uses raw plot coordinates!
	    self.pm.draw_rectangle(self.GCFullPNMap[aFullPNString],gtk.TRUE,x0,y0,width,heigth)
	    self.theWidget.queue_draw_area(x0,y0,width,heigth)

	def drawxorbox(self,x0,y0,x1,y1):
	    newgc=self.pm.new_gc()
	    newgc.set_function(gtk.gdk.INVERT)
	    self.pm.draw_rectangle(newgc,gtk.TRUE,x0,y0,x1-x0,y1-y0)
	    self.theWidget.queue_draw_area(x0,y0,x1,y1)

	def drawtext(self,aFullPNString,x0,y0,text):
		t=str(text)
		self.pm.draw_text(self.font,self.GCFullPNMap[aFullPNString],x0,y0+self.ascent,t)
		self.theWidget.queue_draw_area(x0,y0,self.font.string_width(t),self.ascent+self.descent)

	def shiftplot(self,realshift):
	    #save plotarea
	    self.pm2.draw_drawable(self.pm2.new_gc(),self.pm,self.origo[0]+realshift,
			self.plotarea[1],0,0,self.plotarea[2]-realshift,
			self.plotarea[3]+1)
	    self.clearplotarea()
	    #paste
	    self.pm.draw_drawable(self.pm.new_gc(),self.pm2,0,0,self.origo[0],
			self.plotarea[1],self.plotarea[2]-realshift,
			self.plotarea[3]+1)
	    self.theWidget.queue_draw()
	    self.printTraceLabels()

	def printxlabel(self, num):
	    text=self.num_to_sci(num)
	    x=self.convertx_to_plot(num)
	    y=self.xaxis_y+10
	    self.drawtext("pen",x-self.font.string_width(str(text))/2,y,text)
	    self.drawline("pen",x,self.xaxis_y,x,self.xaxis_y+5)
	    
	def printylabel(self,position,num):
	    text=self.num_to_sci(num)
	    x=self.yaxis_x-5-self.font.string_width(text)
	    y=self.converty_to_plot(num)
	    self.drawtext("pen",x,y-7,text)
	    self.drawline("pen",self.yaxis_x-5,y,self.yaxis_x,y)
	    
	    
	def num_to_sci(self,num):
	    if (num<0.00001 and num>-0.00001 and num!=0) or num >999999 or num<-9999999:
		si=''
		if num<0: 
		    si='-'
		    num=-num
		ex=floor(log10(num))
		m=float(num)/pow(10,ex)
		t=join([si,str(m)[0:4],'e',str(ex)],'')
		return str(t[0:8])
		
	    else:
		return str(num)[0:8]
	    
	def getWidget(self):
	    return self.theWidget 
	    
	def getmaxtraces(self):
	    return len(self.ColorList)
	    
	def convertx_to_plot(self,x):
	    pass
	    
	    
	def reframey(self):  #no redraw!
	    #get max and min from databuffers
	    if self.zoomlevel==0:
		self.getminmax()
		if self.minmax[0]==self.minmax[1]:
		    if self.minmax[0]==0:
			self.minmax[1]=1
		    else:
			self.minmax[1]=self.minmax[0]+abs(self.minmax[0])
		#calculate yframemin, max
		if self.scale_type=='linear':
		    yrange=(self.minmax[1]-self.minmax[0])/(self.yframemax_when_rescaling-self.yframemin_when_rescaling)
		    self.yframe[1]=self.minmax[1]+(1-self.yframemax_when_rescaling)*yrange
		    if self.minmax[0]<0:
			self.yframe[0]=self.minmax[0]-(self.yframemin_when_rescaling*yrange)
		    else: self.yframe[0]=0
		    if self.yframe[0]==self.yframe[1]:self.yframe[1]=self.yframe[0]
		    exponent=pow(10,floor(log10(self.yframe[1]-self.yframe[0])))
		    mantissa1=ceil(self.yframe[1]/exponent)
		    mantissa0=abs(floor(self.yframe[0]/exponent))
		    if mantissa1<=1.0:mantissa1=1.0
		    elif mantissa1<=2.0:mantissa1=2.0
		    elif mantissa1<=5.0:mantissa1=5.0
		    else: mantissa1=10.0
		    
		    self.yticks_no=self.max_yticks_no
		    if self.yframe[0]<0:
			if mantissa0<=1.0:mantissa0=1.0
			elif mantissa0<=2.0:mantissa0=2.0
			elif mantissa0<=5.0:mantissa0=5.0
			else: mantissa0=10.0
			
			if mantissa1>mantissa0:
			    lesser=mantissa0
			    bigger=mantissa1
			else:
			    lesser=mantissa1
			    bigger=mantissa0
			tick_step=bigger/5.0
			lesser_step_no=ceil(lesser/tick_step)
			lesser=tick_step*float(lesser_step_no)
			lesser=int(lesser*1000)
			lesser/=1000.0
			self.yticks_no=5+lesser_step_no
			if mantissa0<mantissa1:
			    mantissa0=lesser
			else:
			    mantissa1=lesser    
		    self.yframe[1]=mantissa1*exponent
		    self.yframe[0]=(-1)*(mantissa0*exponent)
		    self.yticks_step=(self.yframe[1]-self.yframe[0])/self.yticks_no
		else:
		    if self.minmax[0]<0 or self.minmax[1]<=0:
			self.theOwner.theSession.message("negative value in data, fallback to linear scale!\n")
			self.change_scale()
			return
		    if self.minmax[0]==0:
			miny=self.minmax[4]/10
		    else:
			miny=self.minmax[0]
		    self.zerovalue=pow(10,floor(log10(miny)))
		    self.yframe[1]=pow(10,ceil(log10(self.minmax[1])))
		    self.yframe[0]=pow(10,floor(log10(miny)))	    
		    diff=int(log10(self.yframe[1]/self.yframe[0]))
		    if diff==0:diff=1
		    if diff<self.max_yticks_no:
			self.yticks_no=diff
			self.yticks_step=10
		    else:
			self.yticks_no=self.max_yticks_no
			self.yticks_step=pow(10,ceil(diff/self.yticks_no))
		self.ygrid[0]=self.yframe[0]
		self.ygrid[1]=self.yframe[1]

	    else:
		if self.scale_type=='linear':
		    ticks=0
		    if self.yframe[1]==self.yframe[0]:self.yframe[1]=self.yframe[0]+1
		    exponent=pow(10,floor(log10(self.yframe[1]-self.yframe[0])))
		    while ticks<self.max_yticks_no/2:
			mantissa1=floor(self.yframe[1]/exponent)
			mantissa0=ceil(self.yframe[0]/exponent)
			ticks=mantissa1-mantissa0
			if ticks<self.max_yticks_no/2: exponent=exponent/2
			
		    if ticks>self.max_yticks_no:
			mantissa0=ceil(mantissa0/2)*2	
			mantissa1=floor(mantissa1/2)*2
			ticks=(mantissa1-mantissa0)/2
		    self.yticks_no=ticks
		    self.ygrid[1]=mantissa1*exponent
		    self.ygrid[0]=mantissa0*exponent
		    		    		
		    self.yticks_step=(self.ygrid[1]-self.ygrid[0])/self.yticks_no
		
		#scale is log
		else:	
		    if self.yframe[1]>0 and self.yframe[0]>0:
			self.ygrid[1]=pow(10,floor(log10(self.yframe[1])))
			self.ygrid[0]=pow(10,ceil(log10(self.yframe[0])))	    
			diff=int(log10(self.ygrid[1]/self.ygrid[0]))
			if diff==0:diff=1
			if diff<self.max_yticks_no:
			    self.yticks_no=diff
			    self.yticks_step=10
			else:
			    self.yticks_no=self.max_yticks_no
			    self.yticks_step=pow(10,ceil(diff/self.max_yticks_no))
		    else:
			self.theOwner.theSession.message("negative value in range, falling back to linear scale")		
			self.change_scale()
			return
	    self.reframey2()
	    return 0


	def reframey2(self):
	    if self.scale_type=='linear':
		self.pixelheigth=float(self.yframe[1]-self.yframe[0])/self.plotarea[3]
	    else:
		self.pixelheigth=float(log10(self.yframe[1])-log10(self.yframe[0]))/self.plotarea[3]
	    #reprint_ylabels
	    self.reprint_ylabels()

	def converty_to_plot(self,y):
	    if self.scale_type=='linear':
		return self.origo[1]-round((y-self.yframe[0])/float(self.pixelheigth))
	    else:
		return self.origo[1]-round((log10(max(y,self.zerovalue))-log10(self.yframe[0]))/self.pixelheigth)


	def change_scale(self):
    	    #change variable
	    if self.scale_type=='linear': 
		self.scale_type='log10'
	    else:
		self.scale_type='linear'
	    self.reframey()
	    self.drawall()
	    self.definemeasures()
	    if self.scale_type=='linear':
		self.theOwner.set_scale_button( 'Log10 Scale')
	    else:
		self.theOwner.set_scale_button('Linear Scale')


	def reprint_ylabels(self):
	    #clears ylabel area
	    self.clearylabelarea()
	    tick=1
	    if self.scale_type=='linear':
		for tick in range(self.yticks_no+1):
		    tickvalue=self.ygrid[0]+tick*self.yticks_step
		    self.printylabel(tick,tickvalue)
	    else:
		tickvalue=self.ygrid[1]
		while tickvalue>self.ygrid[0]:
		    self.printylabel(tick,tickvalue)
		    tickvalue=tickvalue/self.yticks_step
		self.printylabel(tick,self.ygrid[0])	    
	
	    

	def convertx_to_plot(self,x):
	    return round((x-self.xframe[0])/float(self.pixelwidth))+self.origo[0]
	    
	    
	def convertplot_to_x(self,plotx):
	    return (plotx-self.origo[0])*self.pixelwidth+self.xframe[0]

	    
	def convertplot_to_y(self,ploty):
	    if self.scale_type=='linear':
		return (self.origo[1]-ploty)*self.pixelheigth+self.yframe[0]
	    else:
		return pow(10,(((self.origo[1]-ploty)*self.pixelheigth)+log10(self.yframe[0])))


	def addpoints(self, points):
	    #must be zoom level 0
	    #if strip:
	    redraw_flag=False

	    if self.strip_mode=='strip':
		shift_flag=False
		for fpn in self.data_list:    
		#addbuffer
		    xmax=0
		    self.data_stack[fpn].append(points[fpn])

		    if points[fpn][0]>self.xframe[1]: 
			shift_flag=True
			if points[fpn][0]>xmax: xmax=points[fpn][0]
		    if (points[fpn][1]>self.yframe[1] or points[fpn][1]<self.yframe[0])\
			and self.trace_onoff[fpn]==gtk.TRUE:
			redraw_flag=True
		if shift_flag:
		    newxframe=max(xmax,self.xframe[1]+self.stripinterval*(1-self.xframe_when_rescaling))
		    shift=newxframe-self.xframe[1]
		    self.xframe[1]+=shift
		    self.xframe[0]+=shift
		    self.reframex()
		    for fpn in self.data_list:
			try:
			    while self.data_stack[fpn][1][0]<self.xframe[0]:
				del self.data_stack[fpn][0]
			except IndexError:
			    pass #it's quite normal, that there is no data in frame, because simualtor is too fast
		    realshift=round(shift/self.pixelwidth)
		    if realshift>self.plotarea[2]: redraw_flag=True
		if redraw_flag:
		#if >yframe[1],<yframe[0], reframey, drawall
		    self.reframey()
		    self.drawall()
		elif shift_flag:
		#if >xframe[1],  shiftframe, remove bufferhead 
		    #,adjust lastx, lasty,
		    self.shiftplot(realshift)

		    for fpn in self.data_list:
			if self.lastx[fpn]!=None:
			    self.lastx[fpn]-=realshift
			self.drawpoint(fpn,points[fpn])
		else:
		    for fpn in self.data_list:
			self.drawpoint(fpn,points[fpn])
		#else drawpoint
	    elif self.zoomlevel==0 and not self.zoomkeypressed:
	    #if history:
	    #for each trace:
		if self.requires_scale:
		    self.addtrace([])
		newdata_stack={}
		for fpn in self.data_list:
		    xmax=0
	    #get latest data from logger
		    databuffer=self.data_stack[fpn]
		    if databuffer==[]:
			lasttime=self.xframe[0]
		    else:
			lasttime=databuffer[len(databuffer)-1][0]
		    newdata=self.theOwner.recache(fpn,lasttime,points[fpn][0],self.pixelwidth/2)
	    #addbuffer all
		    databuffer.extend(newdata)
		    newdata_stack[fpn]=[]
		    newdata_stack[fpn].extend(newdata)
	    #check xframe[1], overflow, if yes:addtrace[]
		#if >yframe[1] or<yframe[0], interrupt, addtrace[]
		    if self.trace_onoff[fpn]==gtk.TRUE:
			for dp in newdata:
			    if dp[0]>self.xframe[1]:
				redraw_flag=True
			    if dp[1]>self.yframe[1] or dp[1]<self.yframe[0]:
				redraw_flag=True
		if redraw_flag:
		    self.addtrace([])
		else:
		    for fpn in self.data_list:
			newdata=newdata_stack[fpn]
			for dp in newdata:
			    self.drawpoint(fpn,dp)
	    #begin drawing
		#drawpoint


	def setmode_strip(self,pointmap):
	    #delete buffers
	    #reframe buffers end-interval/end
	    self.refresh_loggerstartendmap()
	    #adjust xframe
	    self.xframe[1]=0
	    for fpn in self.data_list:
	        if pointmap[fpn][0]>self.xframe[1]:
		    self.xframe[1]=pointmap[fpn][0]
	    self.xframe[0]=floor(self.xframe[1]/self.stripinterval)*self.stripinterval
	    if self.xframe[0]<0: self.xframe[0]=0
	    self.xframe[1]=self.xframe[0]+self.stripinterval	
	    #try to get whole data within given xframes		
	    self.reframex()
	    #try to get data from loggers
	    for fpn in self.data_list:
		self.data_stack[fpn]=self.getxframe_from_logger(fpn)
		
	    for fpn in self.data_list:
		self.data_stack[fpn].append(pointmap[fpn]) #latest value
	    self.reframey() 
	    #reframey
	    self.drawall()
	    self.strip_mode='strip'
	    self.zoomlevel=0
	    self.zoombuffer=[]
	    self.zoomkeypressed=False
	    #drawall
	    #zoomlevel=0
	    #mode=strip

	    
	def setmode_history(self):
	    #reframe buufers start/end
	    #get data from loggers
	    self.zoomlevel=0
	    self.zoombuffer=[]
	    self.zoomkeypressed=False

	    #reframey
	    self.strip_mode='history'
	    self.addtrace([])


	def getShortName(self, aFullPN ):
		IdString = str( aFullPN[ID] )
		PropertyString = str( aFullPN[PROPERTY] )
		if PropertyString != 'Value':
			IdString += '/' + PropertyString[:2]
		return IdString
	    
	    
	def addtrace(self,add_list):
	    return_list=[]
	    for add_item in add_list:
	    #checks whether there's room for new traces
	    #allocates a color
		aFullPNString= add_item[0]
		
		pm=self.allocate_color(aFullPNString)
		if pm!=None:
		    self.FullPNMap[aFullPNString]=[add_item[2], self.getShortName(add_item[2])]
		    return_list.append([aFullPNString,pm])

	    #try to get more from logger
	    self.refresh_loggerstartendmap()
	    #if mode is strip
	    if self.strip_mode=='strip':

		#adjust xframe
		for add_item in add_list:
		    if add_item[1][0]>self.xframe[1]:
			self.xframe[1]=add_item[1][0]
			self.xframe[0]=self.xframe[1]-self.stripinterval*self.xframe_when_rescaling

		if self.xframe[0]<0: self.xframe[0]=0
		self.xframe[1]=self.xframe[0]+self.stripinterval	
		#try to get whole data within given xframes		
		self.reframex()
		for fpn in self.data_list:
		    self.data_stack[fpn]=self.getxframe_from_logger(fpn)
		
		for add_item in add_list:
		    fpn=add_item[0]
		    newdatabuffer=self.data_stack[fpn]
		    newdatabuffer.append(add_item[1]) #latest value
		self.reframey()

	    elif self.zoomlevel==0:
		#if mode is history and zoom level 0, set xframes
		self.xframe[0]=None
		self.xframe[1]=None
		self.requires_scale=gtk.TRUE
		for fpn in self.data_list:
		    if self.xframe[0]==None: self.xframe[0]=self.loggerstartendmap[fpn][0]
		    if self.xframe[1]==None: self.xframe[1]=self.loggerstartendmap[fpn][1]
		    if self.loggerstartendmap[fpn][0]<self.xframe[0]:
			self.xframe[0]=self.loggerstartendmap[fpn][0]
			
		    if self.loggerstartendmap[fpn][1]>self.xframe[1]:
			self.xframe[1]=self.loggerstartendmap[fpn][1]
			
		xframe=self.xframe[1]-self.xframe[0]
		if xframe==0: 
		    xframe=self.stripinterval
		else:
		    self.requires_scale=gtk.FALSE
		self.xframe[1]=self.xframe[0]+xframe/self.xframe_when_rescaling
		self.reframex()
		#get all data
		for fpn in self.data_list:
			self.data_stack[fpn]=self.getxframe_from_logger(fpn)
		#getminmax
		self.reframey()
		    
	    else: #just get data from loggers
		self.reframex()
		self.reframey()
		for fpn in self.data_list:
		    self.data_stack[fpn]=self.getxframe_from_logger(fpn)

	    #reframey
	    #drawall
	    self.drawall()
	    self.definemeasures()
	    return return_list


	def getminmax(self):
	    self.minmax=[0,1,0,100,10000000000]
	    #search
	    a=[]
	    for fpn in self.data_list:
		if self.trace_onoff[fpn]:
		    a.extend(self.data_stack[fpn])
	    #init values
	    if len(a)>0:
		self.minmax[0]=a[0][1] #minimum value of all
		self.minmax[1]=a[0][1] #maximum value of all
		self.minmax[2]=a[0][0] #minimum time of all
		self.minmax[3]=a[0][0] #maximum time of all
		for datapoint in a:
		    if self.minmax[0]>datapoint[1]: self.minmax[0]=datapoint[1]
		    if self.minmax[1]<datapoint[1]: self.minmax[1]=datapoint[1]
		    if self.minmax[2]>datapoint[0]: self.minmax[2]=datapoint[0]
		    if self.minmax[3]<datapoint[0]: self.minmax[3]=datapoint[0]
	    	    if datapoint[1]>0:
			if self.minmax[4]>datapoint[1]: self.minmax[4]=datapoint[1]


	def refresh_loggerstartendmap(self):
	    self.loggerstartendmap={}
	    for fpn in self.data_list:
		if self.theOwner.haslogger(fpn):
		    start=self.theOwner.getloggerstart(fpn)
		    end=self.theOwner.getloggerend(fpn)
		    self.loggerstartendmap[fpn]=[start,end]
		else: self.loggerstartendmap[fpn]=[None,None]

	
	def getxframe_from_logger(self,fpn): #refreshes the whole displayed interval 
	    newdatabuffer=[]
    	    data_from=max(min(self.xframe[0],self.loggerstartendmap[fpn][1]),self.loggerstartendmap[fpn][0])
	    data_to=min(self.xframe[1],self.loggerstartendmap[fpn][1])
	    if self.theOwner.haslogger(fpn):
		newdatabuffer=self.theOwner.recache(fpn,data_from,
			    data_to, self.pixelwidth/2)
	    return newdatabuffer

	
	def remove_trace(self, FullPNStringList):
	    #call superclass
	    self.remove_color(FullPNStringList)
	    #redraw
	    for fpn in FullPNStringList:
		self.data_list.remove(fpn)
		self.data_stack.__delitem__(fpn)
		self.FullPNMap.__delitem__(fpn)
		if self.trace_onoff.has_key(fpn):
		    self.trace_onoff.__delitem__(fpn)
	    self.reframey()
	    self.drawall()
	    self.definemeasures()

	
	def press(self,obj, event):
	    x=event.x
	    y=event.y
	    button=event.button
	    #if button is 1
	    if button==1:
		tstamp=event.get_time()
		if self.button_timestamp==tstamp: 
			if self.size_status=='minimized':
				self.maximize()
			else:
				self.minimize_action()
		elif self.GUI_Button_Shown: 
			print x,y
			if x > self.gui_button_area[0] and x< (self.gui_button_area[0]+self.gui_button_area[2]) and\
				y > self.gui_button_area[1] and y<(self.gui_button_area[3]+self.gui_button_area[1]):
				self.maximize()

		self.button_timestamp=tstamp			
		if self.strip_mode=='history':
		#check that mode is history 
		    self.zoomkeypressed=True
		    self.x0=x
		    self.y0=y
		    self.x0=max(self.plotarea[0],self.x0)
		    self.y0=max(self.plotarea[1],self.y0)
		    self.x0=min(self.plotarea[2]+self.plotarea[0],self.x0)
		    self.y0=min(self.plotarea[3]+self.plotarea[1],self.y0)
		    self.x1=self.x0
		    self.y1=self.y0
		    self.realx0=self.x0
		    self.realx1=self.x0
		    self.realy0=self.y0
		    self.realy1=self.y0
	        #create self.x0, y0
	    #if button is 3 and zoomlevel>0
	    elif button==3:
		if self.zoomlevel>0:
		    self.zoomout()
	    	#call zoomout

	    	
	def motion(self,obj,event):
	    #if keypressed undo previous  one
	    if self.zoomkeypressed:
		self.drawxorbox(self.realx0,self.realy0,self.realx1,self.realy1)
		#check whether key is still being pressed, if not cease selection
		x=event.x
		y=event.y
		state=event.state
		if not (gtk.gdk.BUTTON1_MASK & state):
		    self.zoomkeypressed=False
		else:
		    #get new coordinates, sort them
		    #check whether there is excess of boundaries, adjust coordinates
		    self.x1=max(self.plotarea[0],x)
		    self.y1=max(self.plotarea[1],y)
		    self.x1=min(self.plotarea[2]+self.plotarea[0],self.x1)
		    self.y1=min(self.plotarea[3]+self.plotarea[1],self.y1)
		    #get real coordinates
		    self.realx0=min(self.x0,self.x1)
		    self.realx1=max(self.x0,self.x1)
		    self.realy0=min(self.y0,self.y1)
		    self.realy1=max(self.y0,self.y1)
		    #draw new rectangle
	    	    self.drawxorbox(self.realx0,self.realy0,self.realx1,self.realy1)


	def release(self,obj,event):
	    #check that button 1 is released and previously keypressed was set
	    if self.zoomkeypressed and event.button==1:
		#draw old inverz rectangle
	    	self.drawxorbox(self.realx0,self.realy0,self.realx1,self.realy1)
    		#call zoomin	
		if self.realx0<self.realx1 and self.realy0<self.realy1:
		    newxframe=[0,0]
		    newyframe=[0,0]
		    newxframe[0]=self.convertplot_to_x(self.realx0)
		    newxframe[1]=self.convertplot_to_x(self.realx1)
		    newyframe[0]=self.convertplot_to_y(self.realy0)
		    newyframe[1]=self.convertplot_to_y(self.realy1)
		    self.zoomin(newxframe,newyframe)
		self.zoomkeypressed=False
	    

	def zoomin(self, newxframe, newyframe):
	    #increase zoomlevel
	    self.zoomlevel+=1
	    #add new frames to zoombuffer
	    self.zoombuffer.append([[self.xframe[0],self.xframe[1]],
				    [self.yframe[0],self.yframe[1]]])
	    self.xframe[0]=newxframe[0]
	    self.xframe[1]=newxframe[1]
	    self.yframe[0]=newyframe[1]
	    self.yframe[1]=newyframe[0]
	    self.addtrace([])
	    

	def zoomout(self):
	    #if zoomlevel 0 do nothing
	    if self.zoomlevel==1:
		self.setmode_history()
	    #if zoomlevel 1 delete zoombuffer call setmode('history')
	    elif self.zoomlevel>1:
		self.zoomlevel-=1
		newframes=[]
		newframes=self.zoombuffer.pop()
		self.xframe[0]=newframes[0][0]
		self.xframe[1]=newframes[0][1]
		self.yframe[0]=newframes[1][0]
		self.yframe[1]=newframes[1][1]
		self.addtrace([])
		


	def getstripinterval(self):
	    return self.stripinterval
	

	def setstripinterval(self,newinterval):
	    #calulates new xframes, if there are more data in buffer
	    self.stripinterval=newinterval
	    if self.strip_mode=='strip':
		oldinterval=self.xframe[1]-self.xframe[0]
		shift=newinterval-float(oldinterval)
		if shift<0:
		    self.xframe[0]-=shift
		    for fpn in self.data_list:
			databuffer=self.data_stack[fpn]
			if len(databuffer)>0:
			    if databuffer[len(databuffer)-1][0]<self.xframe[0]:
				self.xframe[0]=databuffer[len(databuffer)-1][0]
				self.xframe[1]=self.xframe[0]+newinterval
				databuffer=[]
			    else:
				while self.data_stack[fpn][0][0]<self.xframe[0]:
				    del self.data_stack[fpn][0]
		    self.reframey()

		else:
		    self.xframe[1]+=shift
		self.reframex()
		self.drawall()
	    #reframey 
	    #redrawall


	def getstripmode(self):
	    return self.strip_mode


	def reprint_xlabels(self):
	    #clears xlabel area
	    self.clearxlabelarea()
	    for tick in range(self.xticks_no+1):
		tickvalue=self.xgrid[0]+tick*self.xticks_step
		self.printxlabel(tickvalue)


	def printTraceLabels(self):
	    if self.size_status!='minimized':
		return
	    _textshift=10
	    for fpn in self.data_list:
		if not self.trace_onoff[fpn]:
			continue

		theSum = 0
		theNum = 0

		for dp in self.data_stack[fpn]:
			if dp[1] <= self.yframe[1] and dp[1] >= self.yframe[0]:
				theSum += dp[1]
				theNum += 1

		if  theNum != 0 :
			theAvg = theSum / theNum
			theAvgPos = self.converty_to_plot(theAvg)

		elif len(self.data_stack[fpn]) == 0:
			theAvgPos = _textshift + self.plotaread[1]
		else:
			continue
		
		if theAvgPos < self.plotaread[1] or theAvgPos > self.plotaread[3] + 10 :
			break
		_bias = 10
		if theAvgPos - self.plotaread[1] > self.plotaread[3] - theAvgPos:
			_bias = -15

		self.drawtext( "background", self.plotaread[0] + _textshift + 2, theAvgPos + _bias - 2, \
			self.FullPNMap[fpn][1] )
		self.drawtext( "background", self.plotaread[0] + _textshift + 1, theAvgPos + _bias - 1, \
			self.FullPNMap[fpn][1] )

		self.drawtext( fpn, self.plotaread[0] + _textshift, theAvgPos + _bias, \
			self.FullPNMap[fpn][1] )
		_textshift += 20		


	def drawall(self):
	    #clears plotarea
	    self.clearplotarea()
	    #go trace by trace and redraws plot
	    for fpn in self.data_list:
		if self.trace_onoff[fpn]:
		    self.drawtrace(fpn)

	    self. printTraceLabels()

	
	def drawtrace(self, aFullPNString):
	    #get databuffer, for each point draw
	    databuffer=self.data_stack[aFullPNString][:]
	    self.lastx[aFullPNString]=None	
	    self.lasty[aFullPNString]=None
	    for datapoint in databuffer:
		self.drawpoint(aFullPNString, datapoint)
	    fpn = aFullPNString


	def withinframes(self,point):
	    return point[0]<self.plotaread[2] and point[0]>self.plotaread[0] and\
		   point[1]<=self.plotaread[3] and point[1]>=self.plotaread[1]


	def drawpoint(self, aFullPNString, datapoint):
	    #get datapoint x y values
	    #convert to plot coordinates
	    if self.trace_onoff[aFullPNString]==gtk.FALSE:
		return 0
	    x=self.convertx_to_plot(datapoint[0])
	    y=self.converty_to_plot(datapoint[1])
	    cur_point_within_frame=self.withinframes([x,y])
	    #getlastpoint, calculate change to the last
	    lastx=self.lastx[aFullPNString]
	    lasty=self.lasty[aFullPNString]
	    self.lastx[aFullPNString]=x
	    self.lasty[aFullPNString]=y
	    last_point_within_frame=self.withinframes([lastx,lasty])
	    if lastx!=None:
		dx=abs(lastx-x)
		dy=abs(lasty-y)
	    else:
		dx=0
		dy=0
	    if dx<2 and dy<2:
		#draw just a point
		if cur_point_within_frame:
		    self.drawpoint_on_plot(aFullPNString,x,y)
	    else:
		#draw line    
		if (not cur_point_within_frame) and (not last_point_within_frame):
		    #if neither points are in frame do not draw line
		    pass
		else:
		    #draw line
		    x0=lastx
		    y0=lasty
		    x1=x
		    y1=y
		    if cur_point_within_frame and last_point_within_frame:
		    #if both points are in frame no interpolation needed
			pass
		    else:
			#either current or last point out of frame, do interpolation
			
#interpolation section begins - only in case lastpoint or current point is off limits
			#there are 2 boundary cases x0=x1 and y0=y1
			if x0==x1:
			    #adjust y if necessary
			    if y0<self.plotaread[1] and y1>=self.plotaread[1]:
				y0=self.plotaread[1]
			    if y0>self.plotaread[3] and y1<=self.plotaread[3]:
				y0=self.plotaread[3]

			    if y1<self.plotaread[1] and y0>=self.plotaread[1]:
				y1=self.plotaread[1]
			    if y1>self.plotaread[3] and y0<=self.plotaread[3]:
				y1=self.plotaread[3]
	    
			elif y0==y1:
			    #adjust x values if necessary
			    if x0<self.plotaread[0] and x1>=self.plotaread[0]:
				x0=self.plotaread[0]
			    if x0>self.plotaread[2] and x1<=self.plotaread[2]:
				x0=self.plotaread[2]

			    if x1<self.plotaread[0] and x0>=self.plotaread[0]:
				x1=self.plotaread[0]
			    if x1>self.plotaread[2] and x0<=self.plotaread[2]:
				x1=self.plotaread[2]
	    
			else:

    			    #create coordinate equations
			    mx=float(y1-y0)/float(x1-x0)
			    my=1/mx
			    xi=x0
			    yi=y0
			    #check whether either point is out of plot area
	    
			    #if x0 is out then interpolate x=leftside, create new x0, y0
			    if x0<self.plotaread[0]:
				x0=self.plotaread[0]
				y0=yi+round((x0-xi)*mx)
			    #if y0 is still out, interpolate y=upper and lower side, 
			    #whichever x0 is smaller, create new x0
			    if y0<self.plotaread[1] or y0>self.plotaread[3]:
				#upper side
				y0=self.plotaread[1]
				x0=xi+round((y0-yi)*my)
				#lower side
				y02=self.plotaread[3]
				x02=xi+round((y02-yi)*my)
				if x02<x0:
				    x0=x02
				    y0=y02
			    #repeat it with x1 and y1, but compare to left side
			    if x1>self.plotaread[2]:
				x1=self.plotaread[2]
				y1=yi+round((x1-xi)*mx)
			    #if y0 is still out, interpolate y=upper and lower side, 
			    #whichever x0 is smaller, create new x0
			    if y1<self.plotaread[1] or y1>self.plotaread[3]:
				#upper side
				y1=self.plotaread[1]
				x1=xi+round((y1-yi)*my)
				#lower side
				y12=self.plotaread[3]
				x12=xi+round((y12-yi)*my)
				if x12>x1:
				    x1=x12
				    y1=y12
#interpolation section ends
		    self.drawline(aFullPNString,x0,y0,x1,y1)
		    
		    #if change is 1 pixel in x or y direction drawpoint
		    #else drawline
		    #setlast
	    
	    
	def reframex(self):
		ticks=0
		if self.xframe[0]==self.xframe[1]: self.xframe[1]=self.xframe[0]+100
		exponent=pow(10,floor(log10(self.xframe[1]-self.xframe[0])))
		while ticks < self.max_xticks_no/2:
			mantissa1=floor(self.xframe[1]/exponent)
			mantissa0=ceil(self.xframe[0]/exponent)
			ticks=mantissa1-mantissa0
			if ticks<self.max_xticks_no/2: exponent=exponent/2
		if ticks > self.max_xticks_no:
			mantissa0=ceil(mantissa0/2)*2
			mantissa1=floor(mantissa1/2)*2
			ticks=(mantissa1-mantissa0)/2
		self.xticks_no=ticks
		self.xgrid[1]=mantissa1*exponent
		self.xgrid[0]=mantissa0*exponent
		self.xticks_step=(self.xgrid[1]-self.xgrid[0])/self.xticks_no
		self.pixelwidth=float(self.xframe[1]-self.xframe[0])/self.plotarea[2]
		self.reprint_xlabels()

	def toggle_trace(self,fpn):
	    if self.trace_onoff.has_key(fpn):
		if self.trace_onoff[fpn]==gtk.TRUE:
		    self.trace_onoff[fpn]=gtk.FALSE
		else:
		    self.trace_onoff[fpn]=gtk.TRUE
		self.reframey()
		self.drawall()
		self.definemeasures()
		return self.trace_onoff[fpn]
	    else:
		return gtk.FALSE

	def isOn (self, fpn ):
		if not self.trace_onoff.has_key( fpn ):
			return None
		return self.trace_onoff[fpn]


	def change_trace_color(self,fpn):
	    current_color=self.ColorFullPNMap[fpn]
	    self.deregister_color(fpn)
	    color_index=self.ColorList.index(current_color)
	    color_index=color_index+1
	    if color_index==len(self.ColorList):
		color_index=0
	    pixbuf=self.register_color(fpn,self.ColorList[color_index])
	    self.drawall()
	    return pixbuf

	def minimize_action(self):
		self.theOwner.minimize()

	def minimize(self):
		self.size_status='minimized'		

	
	def maximize(self):
		self.size_status='maximized'
		self.theOwner.maximize()

	def resize( self, args):
		new_width = args[0]
		new_heigth = args[1]
		if new_width==self.plotwidth and new_heigth==self.plotheigth: 
			return
		self.plotwidth=new_width
		self.plotheigth=new_heigth
		self.pm=gtk.gdk.Pixmap(self.theRoot.window,self.plotwidth,self.plotheigth,-1)
		aSizeAlloc= self.theWidget.get_allocation()
		aSizeAlloc[2]=self.plotwidth
		aSizeAlloc[3]=self.plotheigth
		self.theWidget.size_allocate(aSizeAlloc)
		self.recalculate_size()
		self.clearplot()
		self.drawaxes()
		self.reframey()
		self.reframex()
		self.drawall()
		self.draw_gui_button()
		self.drawmeasures()

	def drawmeasures( self ):
		# delete x area
		self.drawbox("background", self.xmes_ltop[0], self.xmes_ltop[1], 100, 20)

		# drawtext xmes
		self.drawtext("pen", self.xmes_ltop[0], self.xmes_ltop[1], self.xmes )

		# delete y area
		self.drawbox("background", self.ymes_ltop[0], self.ymes_ltop[1], 200, 20)

		# drawtext ymes
		self.drawtext("pen", self.ymes_ltop[0], self.ymes_ltop[1], self.ymes )		


	def definemeasures ( self ):
		# xmes is sec
		self.xmes='sec'

		# get all displayed fullpns
		# for all fpn
		mes_list ={}
		for fpn in self.data_list:
		    if self.trace_onoff[fpn]:
			# get type and propertyname
			anArray= fpn.split(':')
			aType = anArray[0]
			aProperty = anArray[3]

			# define values from measure list
			aMeasure='??'
			for aMeasureItem in self.mes_dict:
				if aMeasureItem[0]==aType and aMeasureItem[1]==aProperty:
					aMeasure= aMeasureItem[2]
					break

			# add it to measure list
			mes_list[aMeasure]=1
		# consolidate measure list
		mes_keys = mes_list.keys()
		if len(mes_keys)>1:

			# if there are diferent measures it is 'mixed measures'
			self.ymes ='mixed measures'

		elif len(mes_keys) ==1:
			self.ymes = mes_keys[0]
		else:
			self.ymes=''

		# add scale information
		self.ymes = self.ymes + "    " + self.scale_type + " scale"
		self.drawmeasures()
		
