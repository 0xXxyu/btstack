#!/usr/bin/env python
import os
import re
import sys 

docs_folder = ""
appendix_file = docs_folder + "examples.tex"

lst_header = """
\\begin{lstlisting}
"""

lst_ending = """
\end{lstlisting}
"""

example_header = """
\documentclass[11pt, oneside]{article}      
\usepackage{geometry}                       
\geometry{letterpaper}                         
%\geometry{landscape}                       
%\usepackage[parfill]{parskip}          
\usepackage{graphicx}                     
\usepackage{amssymb}
\usepackage{listings}
\usepackage{hyperref}
\\begin{document}
\section{Examples}
"""

example_ending = """
\end{document}  
"""

example_item = """
    \item \emph{EXAMPLE_TITLE}: EXAMPLE_DESC, see Section \\ref{example:EXAMPLE_LABLE}.
"""
example_section = """
\subsection{EXAMPLE_TITLE: EXAMPLE_DESC}
\label{example:EXAMPLE_LABLE}

"""
example_subsection = """
\subsubsection{LISTING_CAPTION}
"""

listing_start = """
\\begin{lstlisting}[float, caption= LISTING_CAPTION., label=listing:LISTING_LABLE]
"""

listing_ending = """\end{lstlisting}

"""
msp_folder = "../../platforms/msp-exp430f5438-cc2564b/example/"
embedded_folder = "../../example/embedded/"
# Example group title: [folder, example file, section title]
list_of_examples = { 
    #"UART" : [[msp_folder, "led_counter", "UART and timer interrupt without Bluetooth"]
    "GAP"  : [[embedded_folder, "gap_inquiry", "GAP Inquiry Example"]],
    #"SPP Server" : [[embedded_folder, "spp_counter", "SPP Server - Heartbeat Counter over RFCOMM"],
    #                [embedded_folder, "spp_accel", "SPP Server - Accelerator Values"],
    #                [embedded_folder, "spp_flowcontrol", "SPP Server - Flow Control"]],
    #"HID Host" :[[embedded_folder, "hid_demo", "HID Demo"]],
    #"Low Energy" :[[embedded_folder, "gatt_browser", "GATT Client - Discovering primary services and their characteristics"],
    #                [embedded_folder, "ble_server", "LE Peripheral"]],
    #"Dual Mode " :[[embedded_folder, "spp_and_le_counter", "Dual mode example"]],
    #"SDP BNEP Query" :[[embedded_folder, "sdp_bnep_query", "SDP BNEP Query"]],
}

class State:
    SearchExampleStart = 0
    SearchListingStart = 2
    SearchListingPause = 4
    SearchListingResume = 5
    SearchListingEnd = 6
    SearchItemizeEnd = 7
    ReachedExampleEnd = 8

def replacePlaceholder(template, title, lable):
    snippet = template.replace("API_TITLE", title).replace("API_LABLE", lable)
    return snippet


def writeListings(fout, infile_name):
    itemText = None
    state = State.SearchExampleStart

    with open(infile_name, 'rb') as fin:
        for line in fin:
            if state == State.SearchExampleStart:
                parts = re.match('.*(EXAMPLE_START)\((.*)\):\s*(.*)(\*/)?\n',line)
                if parts: 
                    lable = parts.group(2)
                    title = parts.group(2).replace("_","\_")
                    desc  = parts.group(3).replace("_","\_")
                    print desc
                    aout.write(example_section.replace("EXAMPLE_TITLE", title).replace("EXAMPLE_DESC", desc).replace("EXAMPLE_LABLE", lable))
                    state = State.SearchListingStart
                continue
            
            if itemText:
                itemize_new = re.match('(\s*\*\s*\-\s*)(.*)',line)
                if itemize_new:
                    aout.write(itemText + "\n")
                    itemText = "\item "+ itemize_new.group(2)
                else:
                    empty_line = re.match('(\s*\*\s*)\n',line)
                    comment_end = re.match('\s*\*/.*', line)
                    if empty_line or comment_end:
                        aout.write(itemText + "\n")
                        aout.write("\n\end{itemize}\n")
                        itemText = None
                    else:
                        itemize_continuation = re.match('(\s*\*\s*)(.*)',line)
                        if itemize_continuation:
                            itemText = itemText + " " + itemize_continuation.group(2)
                continue
            
            section_parts = re.match('.*(@section)\s*(.*)\s*(\*?/?)\n',line)
            if section_parts:
                aout.write("\n" + example_subsection.replace("LISTING_CAPTION", section_parts.group(2)))
                continue

            subsection_parts = re.match('.*(@subsection)\s*(.*)\s*(\*?/?)\n',line)
            if section_parts:
                subsubsection = example_subsection.replace("LISTING_CAPTION", section_parts.group(2)).replace('section', 'subsection')
                aout.write("\n" + subsubsection)
                continue

            brief_parts = re.match('.*(@text)\s*(.*)',line)
            if brief_parts:
                brief = "\n" + brief_parts.group(2)
            else:
                brief_parts = re.match('(\s\*\s)(.*)(\*/)?.*',line)
                if brief_parts:
                    brief = " " + brief_parts.group(2)
            
            if brief_parts:
                # replace refs
                refs = re.match('.*(Listing\s*)(\w*).*',brief)
                if refs:
                    brief = brief.replace(refs.group(2), "\\ref{listing"+refs.group(2)+"}")
                refs = re.match('.*(Section\s*)(\w*).*',brief)
                if refs:
                    brief = brief.replace(refs.group(2), "\\ref{section:"+refs.group(2)+"}")
                    
                aout.write(brief)
                continue
            else:
                itemize_part = re.match('(\s*\*\s*-\s*)(.*)',line)
                if (itemize_part):
                    aout.write("\n \\begin{itemize}\n")
                    itemText = "\item "+ itemize_part.group(2)

            if state == State.SearchListingStart:
                parts = re.match('.*(LISTING_START)\((.*)\):\s*(.*\s*)(\*/).*',line)
                
                if parts: 
                    lst_lable = parts.group(2)
                    lst_caption = parts.group(3).replace("_","\_")
                    listing = listing_start.replace("LISTING_CAPTION", lst_caption).replace("LISTING_LABLE", lst_lable)
                    if listing:
                        aout.write("\n" + listing)
                    state = State.SearchListingEnd
                continue
            
            if state == State.SearchListingEnd:
                parts_end = re.match('.*(LISTING_END).*',line)
                parts_pause = re.match('.*(LISTING_PAUSE).*',line)
                
                if not parts_end and not parts_pause:
                    end_comment_parts = re.match('.*(\*)/*\s*\n', line);
                    if not end_comment_parts:
                        aout.write(line)
                elif parts_end:
                    aout.write(listing_ending)
                    state = State.SearchListingStart
                elif parts_pause:
                    aout.write("...\n")
                    state = State.SearchListingResume
                continue
                
            if state == State.SearchListingResume:
                parts = re.match('.*(LISTING_RESUME).*',line)
                if parts:
                    state = State.SearchListingEnd
                continue
        
            parts = re.match('.*(EXAMPLE_END).*',line)
            if parts:
                if state != State.SearchListingStart:
                    print "Formating error detected"
                state = State.ReachedExampleEnd
                print "Reached end of the example"
            
    

# write list of examples
with open(appendix_file, 'w') as aout:
    aout.write(example_header)
    aout.write("\\begin{itemize}\n");
    
    for group_title, examples in list_of_examples.iteritems():
        group_title = group_title + " example"
        if len(examples) > 1:
            group_title = group_title + "s"
        group_title = group_title + ":"

        aout.write("  \item " + group_title + "\n");
        aout.write("  \\begin{itemize}\n");
        for example in examples:
            lable = example[1]
            title = example[1].replace("_","\_")
            desc = example[2].replace("_","\_")
            aout.write(example_item.replace("EXAMPLE_TITLE", title).replace("EXAMPLE_DESC", desc).replace("EXAMPLE_LABLE", lable))
        aout.write("  \\end{itemize}\n")
    aout.write("\\end{itemize}\n")

    for group_title, examples in list_of_examples.iteritems():
        for example in examples:
            file_name = example[0] + example[1] + ".c"
            writeListings(aout, file_name)

    aout.write(example_ending)
