"""
This program is meatn to comapre the input files (.inp)
of a pre and post developed mode. The differences will be
outputed into a report that hightlight what is new or changed.

Utilizes the pyswmm library for its SWMM analysis tools

A highlight_Subcatchment is defined as a subcatchment that is not in the original model (new) or
a old subcatchment that has been deleted (missing in post developed model.) This helps the reviewer
know which subcatchments to look at before starting a model review. 

6/10/20: Started work on based code
"""

import difflib, os, re
from operator import attrgetter
from pyswmm import Simulation, Subcatchments

# Creating classes to define the change objects that reflect the differences
class highlight_Subcatchment:
    #The important variables to check inputs. Should look into inheriting the parent class
    def __init__(self, name, area, connection, percent_impervious,
                 slope, width):
        self.name = name # subcatchment name
        self.area = area # subcatchment area in acres
        self.connection = connection # subcatchment connection, stores a 2 item list surface loading type & downstreamconnection. 
        self.percent_impervious = percent_impervious # subcatchment impervious cover
        self.slope = slope # subcatchment slope in ft./ft.
        self.width = width # subcatchment width in ft.
        
    def __eq__(self, other):
        if not isinstance(other, highlight_Subcatchment):
            return NotImplemented
        return self.name == other.name and self.area == other.area and self.connection == other.connection and self.percent_impervious == other.percent_impervious and self.slope == other.slope and self.width == other.width    

# Creating a function that loops through a model's subcatchments against a name list and checks if the name is in or not
# If it is not, then it stores and returns a list of subcatchment objects. Also returns the sum of all areas.
def iterate_subcatchments(input_file, name_list):
    subcatchment_objects = Subcatchments(Simulation(input_file)) #retrieves model data and stores in the subcatchment_objects list(idk if it is even a list)
    all_subcatchments = [] # initialize an empty list to contain all subcatchments
    delta_subcatchments = [] # initialize an empty list to contain the new subcatchments
    area = 0 #initialize an empty function variable to add and store total areas
    for i in subcatchment_objects:
        area += i.area
        if i.subcatchmentid not in name_list: #if subcatchment name is not in the given name list, then store it in the empty list
            delta_subcatchments.append(highlight_Subcatchment(i.subcatchmentid, i.area, i.connection[1], i.percent_impervious, i.slope, i.width)) #only the first arguemtn of i.connection is relevant for the report
        else:
            all_subcatchments.append(highlight_Subcatchment(i.subcatchmentid, i.area, i.connection[1], i.percent_impervious, i.slope, i.width))
    all_subcatchments.sort(key=attrgetter('name'))
    return all_subcatchments, delta_subcatchments, area

#creating a function to compare pre and post subcatchments
def compare_subcatchments(pre_list, post_list):
    if len(pre_list) != len(post_list):
        print('ERROR AT COMPARE SUBCATCHMENTS FUNCTION')
        return
    modified_pre_list = []
    modified_post_list = []
    for i in range(len(pre_list)):
        if pre_list[i] != post_list[i]:
            modified_pre_list.append(pre_list[i])
            modified_post_list.append(post_list[i])
    return modified_pre_list, modified_post_list

# a function to write the results of the highlight_Subcatchments in a report
# this is setup to write in csv form but will be changed later to write in a pdf or word document form
def write_results(subcatchment_list, pre_or_post, report):
    report.write('The following subcatchments are not in the {} model\n'.format(pre_or_post))
    report.write('SUBCATCHMENTID, AREA(acres), DOWNSTREAM_CONNECTION, IMPERVIOUS(%), SLOPE(ft./ft.), WIDTH(ft.)\n')
    for i in subcatchment_list:
        report.write("{}, {}, {}, {}, {}, {}\n".format(i.name, i.area, i.connection, i.percent_impervious*100, i.slope, i.width))
    report.write('\n')

def write_modifiedsubcatchments(pre_list, post_list, func_report):
    func_report.write('The following subcatchments were modified\n')
    func_report.write('PREDEVELOPED')
    func_report.write('SUBCATCHMENTID, AREA(acres), DOWNSTREAM_CONNECTION, IMPERVIOUS(%), SLOPE(ft./ft.), WIDTH(ft.)\n')
    for i in pre_list:
        func_report.write("{}, {}, {}, {}, {}, {}\n".format(i.name, i.area, i.connection, i.percent_impervious*100, i.slope, i.width))
    func_report.write('\nPOST DEVELOPED')
    for i in pre_list:
        func_report.write("{}, {}, {}, {}, {}, {}\n".format(i.name, i.area, i.connection, i.percent_impervious*100, i.slope, i.width))

if __name__ == "__main__":
    
    # runs through a simulation to develop the pre-developed name list for the iterate_subcatchments function
    pre_subcatchments = Subcatchments(Simulation('pre_100.inp'))
    pre_subcatnames = [i.subcatchmentid for i in pre_subcatchments]

    # runs through a simulation to develop the post-developed name list for the iterate_subcatchments function
    post_subcatchments = Subcatchments(Simulation('post_100.inp'))
    post_subcatnames = [i.subcatchmentid for i in post_subcatchments]

    #creates the object lists containing the highlighted subcatchments and the total areas of the pre & post model.
    #currently assumes two files are in the cd named 'pre_100.inp' and 'post_100.inp'
    all_pre_Subcatchments, all_new_Subcatchments, pre_totarea = iterate_subcatchments('pre_100.inp', post_subcatnames)
    all_post_Subcatchments, missing_old_Subcatchments, post_totarea = iterate_subcatchments('post_100.inp', pre_subcatnames)
    modified_pre_subcatchments, modified_post_subcatchments = compare_subcatchments(all_pre_Subcatchments, all_post_Subcatchments)
    
    # creates the report file and writes the results down.
    highlight_report = open('Comparison Report.csv', 'w')
    
    # writes down another hightlight of the report if the total of the two areas are not within 1% of eachother
    if pre_totarea < 0.99*post_totarea or pre_totarea > 1.01*post_totarea:
        highlight_report.write('TOTAL SUBCATCHMENT AREAS ARE NOT THE SAME\n')
        highlight_report.write('Pre Total Area:,{}\nPost Total Area:,{}\n'.format(pre_totarea, post_totarea))
        
    write_results(missing_old_Subcatchments, "predeveloped", highlight_report)
    write_results(all_new_Subcatchments, "postdeveloped", highlight_report)
    write_modifiedsubcatchments(modified_pre_subcatchments, modified_post_subcatchments, highlight_report)
    
    # close the file
    highlight_report.close()

    
    