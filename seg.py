import cv2
import numpy as np
import time
import json
import copy
import numpy as np

COLOR_NAMES = ["Red",
				"Green",
				"Yellow",
				"Blue",
				"Orange",
				"Purple",
				"LightBlue",
				"Pink",
				"Lime",
				"LightPink"]
		
COLOR_PALETTE = [(230, 25, 75),
				(60, 180, 75),
				(255, 225, 25),
				(0, 130, 200),
				(245, 130, 48),
				(145, 30, 180),
				(70, 240, 240),
				(240, 50, 230),
				(210, 245, 60),
				(250, 190, 212)]


class Segmentation:
	def __init__(self,imagePath,nPaws):
		self.image_name = imagePath
		self.imagePath = cv2.imread(imagePath)
		self.nPaws = nPaws
		self.gray = cv2.cvtColor(self.imagePath, cv2.COLOR_BGR2GRAY)
		self.height,self.width = self.gray.shape
		self.image = []
		self.class_label = 2
		self.class_bounds = [[self.width,0]]
		self.nth_class = 0
		self.class_labels = {}

	def threshold(self,image,boundary,min_value,high_value):
		gray = copy.deepcopy(image)
		for row in range(self.height):
			for col in range(self.width):
				if gray[row][col] < boundary:
					gray[row][col] = min_value
				else:
					gray[row][col] = high_value
		return gray

	def swap_row_col(self,gray_image):
		column = []
		for col in range(self.width):
		 	for row in range(self.height):
		 		column.append(gray_image[row][col])
		 	self.image.append(column)
		 	column = []

	def swap_col_row(self,image):
		img = []
		row = []
		for i in range(self.height):
			for j in range(self.width):
				row.append(image[j][i])
			img.append(row)
			row = []
		return img

	def grid_search(self,row,col,depth):
		if not self.image[row][col]:
			self.class_bounds[self.nth_class][0] = min(self.class_bounds[self.nth_class][0],row)
			self.class_bounds[self.nth_class][1] = max(self.class_bounds[self.nth_class][1],row)
			self.image[row][col] = self.class_label
			return all([self.grid_search(row,col-1,depth+1),
						self.grid_search(row,col+1,depth+1),
						self.grid_search(row-1,col,depth+1),
						self.grid_search(row+1,col,depth+1)])
		else:
			return depth


	def pick_pixel(self):
		for row in range(self.width):
			for col in range(self.height):
				if not self.grid_search(row,col,0):
					continue
				else:
					self.class_bounds.append([self.width,0])
					self.class_labels[f"{self.class_bounds[self.nth_class]}"] = self.class_label
					self.class_label+=1
					self.nth_class+=1


	def in_range(self,range1,range2):
		ranges = [range1,range2]
		x_coors = [ranges[0][0],ranges[1][0]]
		index_of_max_x = x_coors.index(max(x_coors))
		if ranges[index_of_max_x][1]<=ranges[index_of_max_x-1][1]:
			return ranges[index_of_max_x]
		else:
			return False

	def change_color(self,image,label,color):
		bg_color = True if label==1 else False
		np_color = [color[2],color[1],color[0]]
		for row in range(len(image)):
			for col in range(len(image[row])):
				if bg_color and not isinstance(image[row][col],list):
						image[row][col] = np_color
				elif image[row][col] == label:
						image[row][col] = np_color
				else:
					pass

		return image

	def handle_error(self,n_to_remove,array_of_bounds):
		nth_color = 0
		color_labelled_dict = {}
		test_image = copy.deepcopy(self.swap_col_row(self.image))
		for x_min,x_max in array_of_bounds:
			test_image = self.change_color(test_image,self.class_labels[f"[{x_min}, {x_max}]"],COLOR_PALETTE[nth_color])
			#cv2.rectangle(test_image,(x_min-1,-1),(x_max+1,self.height+1),COLOR_PALETTE[nth_color],1)
			color_labelled_dict[COLOR_NAMES[nth_color]] = [x_min,x_max]
			nth_color+=1

		test_image = self.change_color(test_image,1,(255,255,255))
		

		test_image = np.array(test_image,dtype=np.uint8)
		cv2.namedWindow(f"{self.image_name}",cv2.WINDOW_NORMAL)
		cv2.resizeWindow(f"{self.image_name}",self.width*5,self.height*5)
		cv2.imshow(f"{self.image_name}",test_image)
		cv2.waitKey()
		for label,coor in color_labelled_dict.items():
			print(f"{label} : {coor}")
		while True:
			rm_list = input(f"Enter {n_to_remove} items (,) to remove: ")
			print("HELLLOO")
			if rm_list == "skip":
				return False
			try:
				rm_list = rm_list.split(",")
				if len(rm_list)==n_to_remove:

					for n in [color_labelled_dict[x] for x in rm_list]:
						array_of_bounds.remove(n)
					break
			except (ValueError,KeyError):
				print("Invalid input!")
		return array_of_bounds


	def filter_class_bounds(self,array):
		elim = set()
		for x,y in array:
			if abs(x-y)==self.width or abs(x-y)==self.height or x==y:
				elim.add(f"[{x}, {y}]")
		for elem in range(len(array)):
			if not elem == len(array):
				for next_elems in range(elem+1,len(array)):
					evaluation = self.in_range(array[elem],array[next_elems])
					if evaluation:
						elim.add(f"{evaluation}")

		elim = [json.loads(n) for n in list(elim)]
		
		for i in elim:
			array.remove(i)
		
		exc_items = len(array) - self.nPaws

		if exc_items:
			array = self.handle_error(exc_items,array)

		return array

	def segment(self):
		gray_image = self.threshold(self.gray,120,0,1)
		self.swap_row_col(gray_image)
		self.pick_pixel()
		return self.filter_class_bounds(self.class_bounds)





