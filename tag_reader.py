#!/usr/bin/python

import math
import binascii

## Class to parse through music file and read data from available tags.
class TagReader:
    filename    = None
    file_handle = None
    tag         = None

    ## Constructor
    #  @param self
    #  @param filename  Location of the file to open. 
    def __init__(self, filename):
        try:
            self.filename    = filename
            self.file_handle = open(filename)
            self.tag         = self.check_tag()
        except IOError:
            print "Unable to open file"


    ## Check if specified bit in byte is set.
    #  @param byte  int representation of a byte
    #  @param index Location of the bit
    #  @return int  1 if set, 0.
    def get_bit(self, byte, index):
        return ((byte & (1 << index)) != 0)


    ###########################################################################
    #                       Version 1                                         #
    #                                                                         #
    #        +-------------------------------------+                          #
    #        |TAG        |  03 char |  -128 to -126|                          #
    #        |Song Title |  30 char |  -125 to -96 |                          #
    #        |Artist     |  30 char |  -95 to -66  |                          #
    #        |Album      |  30 char |  -65 to -36  |                          #
    #        |Year       |  04 char |  -35 to -32  |                          #
    #        |Comment    |  28 char |  -31 to -04  |                          #
    #        |Null char  |  01 byte |  -3          |                          #
    #        |Track      |  01 byte |  -2          |                          #
    #        |Genre      |  01 byte |  -1          |                          #
    #        +-------------------------------------+                          #
    ###########################################################################
    
    ## Read version 1 of ID3
    def id3v1(self):
        try:
            self.file_handle.seek(-128, 2)
            self.file_handle.read(3)   # Identifier
            title  = self.file_handle.read(30)     # Song Title
            artist = self.file_handle.read(30)     # Artist
            album  = self.file_handle.read(30)     # Album
            year   = self.file_handle.read(4)      # Year
            comm   = self.file_handle.read(28)     # Comment
            self.file_handle.read(1)               # Null
            track  = self.file_handle.read(1)      # Track
            genre  = self.file_handle.read(1)      # Genre

            return [title, artist, album, year, comm, track, genre]
        except IOError:
            pass


    ###########################################################################
    #                       Version 2                                         #
    #                                                                         #
    #                       +-----------------------+                         #
    #                       |   Header (10 bytes)   |                         #
    #                       +-----------------------+                         #
    #                       |   Extended Header     |                         #
    #                       |  (Variable length,    |                         #
    #                       |       Optional)       |                         #
    #                       +-----------------------+                         #
    #                       |   Frames (variable    |                         #
    #                       |       length)         |                         #
    #                       +-----------------------+                         #
    #                       |       Padding         |                         #
    #                       |   (Variable length,   |                         #
    #                       |       Optional)       |                         #
    #                       +-----------------------+                         #
    #                       |   Footer (10 bytes,   |                         #
    #                       |       Optional)       |                         #
    #                       +-----------------------+                         #
    ###########################################################################
    
    ## Read the first 10 bytes of the file and return them in a list.
    #  @return tupe (ident, version, revision, flags, size)
    def id3v2_header(self):
        try:
            self.file_handle.seek(0)            # Make sure were at the begining
            ident    = self.file_handle.read(3)
            version  = self.file_handle.read(1)
            revision = self.file_handle.read(1)
            flags    = bytearray(self.file_handle.read(1))
            size     = bytearray(self.file_handle.read(4)) 
            
            return (ident, version, revision, flags, size)
        except IOError:
            pass


    ## Parse for version 2 of ID3v2
    #  Implemented tags:
    #       TT2 Title/Songname/Content description
    #       TP1 Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group
    #       TAL Album/Movie/Show title
    #       TYE Year
    #  @param self
    #  @return Associative array
    def id3v2_2(self):
        data = {'Artist':None, 'Album':None, 'Title':None, 'Year':None, \
            'Comments':None, 'Track':None, 'Genre':None}

        try:
            header = self.id3v2_header() 
            
            #TODO Check if bit 7 of flags is set
            size = (self.id3v2_decode_size(header[4]) - 1) - 10
            
            curr = size
            while curr > 0:
                tag   = self.file_handle.read(3)
                tsize = self.file_handle.read(3)
                curr -= 6

                fsize = 0
                for i in tsize:
                    fsize += ord(i)
    
                val   = self.file_handle.read(fsize)
                curr -= fsize
                if tag == "TT2":
                    data['Title'] = val
                    continue

                if tag == "TAL":
                    data['Album'] = val
                    continue

                if tag == "TP1":
                    data['Artist'] = val
                    continue

                if tag == "TYE":
                    data['Year'] = val
                    continue
            
            return data
        except IOError:
            pass


    ## Decode size of id3v2 tag.
    #  Tag is encoded with four bytes where the first bit is set to zero
    #  in every byte, making a total of 28 bits.
    #  @param bytearray
    #  @return float
    def id3v2_decode_size(self,size):
        total_size = 0
        i = 3 
        j = 0
        t = 0
        while i >= 0:
            j = 0
            while j < 8:
                if j != 7:
                    if self.get_bit(size[i],j) == 1:
                        total_size += math.pow(2,t)
                    t += 1

                j += 1

            i -= 1 

        return total_size


    ## Check if id3v1 tag exists
    #  @return bool
    def check_if_id3v1(self):
        try:
            self.file_handle.seek(-128,2)
            if self.file_handle.read(3) == "TAG":
                return True

            return False
        except IOError:
            pass


    ## Check if id3v2 tag exists
    #  ID3v2 follows the pattern:
    #  $49 $44 $33 yy yy xx zz zz zz zz
    #  Where yy < $FF,
    #    xx is flags byte
    #    zz < $80
    #  @return tupe (false, 0) or (True, version (hex string))
    def check_if_id3v2(self):
        try:
            header = self.id3v2_header()
            if header[0] != "ID3":
                return (False,0)

            if header[1] == 0xFF:
                return (False,0)
            
            if header[2] == 0xFF:
                return (False,0)
            
            size = header[4][0] + header[4][1] + header[4][2] + header[4][3]
            if size >= 128:
                return (False,0)
            
            return (True, header[1])
        except IOError:
            pass

   
    ## Check which tag is available (newest first)
    #  @return tuple (tag, version)
    def check_tag(self):
        # TODO
        #if self.check_if_id3v1():
        #    return ("id3v1",None)
        
        val = self.check_if_id3v2()
        if val[0] == True:
            return ("id3v2", val[1])

        return (None, None)


    ## Read tag based on initial information
    #  @return None if nothin, else associative array.
    def read_tags(self):
        if self.file_handle == None:
            return None

        if self.file_handle.closed:
            self.file_handle = open(self.filename, "r")

        if self.tag[0] == "id3v2":
            if self.tag[1] == "\x02":
                data = self.id3v2_2()
                self.file_handle.close()
                return data
        
        return None
