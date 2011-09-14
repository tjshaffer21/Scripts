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


    ## Check which tag is available (newest first)
    #  @return tuple (tag, version)
    def check_tag(self):
        val = self.check_if_id3v2()
        if val[0] == True:
            return ("id3v2", val[1])

        val = self.check_if_id3v1()
        if val[0] == True:
            return ("id3v1",val[1])
        
        return (None, None)


    ## Check if id3v1 tag exists
    #  @note returned string is "" if normal, "e" if extended
    #  @return tuple (bool, string)
    def check_if_id3v1(self):
        try:
            self.file_handle.seek(-355, 2)
            if self.file_handle.read(4) == "TAG+":
                return (True, "e")

            self.file_handle.seek(-128,2)
            if self.file_handle.read(3) == "TAG":
                return (True, " ")

            return (False, None)
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


    ## Check if specified bit in byte is set.
    #  @param byte  int representation of a byte
    #  @param index Location of the bit
    #  @return int  1 if set, 0.
    def get_bit(self, byte, index):
        return ((byte & (1 << index)) != 0)


    ###########################################################################
    #                   Version 1 Extended                                    #
    #        +-------------------------------------+                          #
    #        |TAG+       |  04 char |  -355 to -352|                          #
    #        |Song Title |  60 char |  -351 to -293|                          #
    #        |Artist     |  60 char |  -292 to -232|                          #
    #        |Album      |  60 char |  -231 to -173|                          #
    #        |Speed      |  01 byte |          -172|                          #
    #        |Genre      |  30 char |  -171 to -141|                          #
    #        |Start-Time |  06 byte |  -140 to -135|                          #
    #        |End-Time   |  06 byte |  -134 to -129|                          #
    #        +-------------------------------------+                          #
    #                                                                         #
    #                       Version 1                                         #
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
    #  @note Format {Artist, Album, Title, Year, Comments, Track, Genre}
    #  @note Genre, Index in list of genres, or 255
    #  @return Associative Array
    def id3v1(self):
        data = {'Artist':None, 'Album':None, 'Title':None, 'Year':None, \
            'Comments':None, 'Track':None, 'Genre':None}
        
        try:
            self.file_handle.seek(-128, 2)
            self.file_handle.read(3)                        # Identifier
            data['Title']   = self.file_handle.read(30)
            data['Artist']  = self.file_handle.read(30)
            data['Album']   = self.file_handle.read(30)
            data['Year']    = self.file_handle.read(4)
            data['Comment'] = self.file_handle.read(28)
            self.file_handle.read(1)
            data['Track']   = self.file_handle.read(1)
            data['Genre']   = ord(self.file_handle.read(1))

            return data
        except IOError:
            pass


    ## Read extended tag of ID3v1
    #  @note Format {Artist, Title, Artist, Album, Speed, Genre, Start-Time,
    #        End-Time}
    #  @note Speed: 0=unset, 1=slow, 2=medium,3=fast,4=hardcore
    #  @note Start-Time, End-Time: mmm:ss
    #  @return Associative Array
    def id3v1_1(self):
        data = {'Artist':None, 'Title':None, 'Artist':None, 'Album':None, \
            'Speed':None, 'Genre':None, 'Start-Time':None, 'End-Time':None}

        try:
            self.file_handle.seek(-355, 2)
            self.file_handle.read(4)                        # Identifier
            data['Title']       = self.file_handle.read(60)
            data['Artist']      = self.file_handle.read(60)
            data['Album']       = self.file_handle.read(60)
            data['Speed']       = self.file_handle.read(1)
            data['Genre']       = self.file_handle.read(30)
            data['Start-Time']  = self.file_handle.read(6)
            data['End-Time']    = self.file_handle.read(6)

            return data
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


    ## Start of ID3v2 family
    #  @return Associative array
    def id3v2(self):
        header = self.id3v2_header() 
            
        version = ord(header[1])
        if version == 2:
            return self.id3v2_2(header)
        elif version == 3 or version == 4:  # TODO: Implement v.4
            return self.id3v2_3(header)


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


    ## Parse for version 2 of ID3v2
    #  Implemented tags:
    #       TT2 Title/Songname/Content description
    #       TP1 Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group
    #       TAL Album/Movie/Show title
    #       TYE Year
    #       TCO Content Type
    #       TRK Track Number
    #  @return Associative array
    def id3v2_2(self,header):
        data = {'Artist':None, 'Album':None, 'Title':None, 'Year':None, \
            'Comments':None, 'Track':None, 'Genre':None}
        try:
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

                if tag == "TCO":
                    data['Genre'] = val
                    continue

                if tag == "TRK":
                    data['Track'] = val
                    continue
            
            return data
        except IOError:
            pass

    
    ## Parse for version  of ID3v2
    #  Implemented tags:
    #       TIT2 Title/Songname/Content description
    #       TPE1 Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group
    #       TALB Album/Movie/Show title
    #       TYER Year
    #       TCON Content Type
    #       TRCK Track Number
    #  @return Associative array
    def id3v2_3(self, header):
        data = {'Artist':None, 'Album':None, 'Title':None, 'Year':None, \
            'Comments':None, 'Track':None, 'Genre':None}
        try:
            #TODO Check if bit 7 of flags is set
            size = (self.id3v2_decode_size(header[4]) - 1) - 10
            
            if self.get_bit(header[3][0], 6):
                pass            # TODO: Implement details for extended header

            curr = size
            while curr > 0:
                tag   = self.file_handle.read(4)
                tsize = self.file_handle.read(4)
                flags = self.file_handle.read(2)
                curr -= 6

                fsize = 0
                for i in tsize:
                    fsize += ord(i)
    
                val   = self.file_handle.read(fsize)
                curr -= fsize
                if tag == "TIT2":
                    data['Title'] = val
                    continue

                if tag == "TALB":
                    data['Album'] = val
                    continue

                if tag == "TPE1":
                    data['Artist'] = val
                    continue

                if tag == "TYER":
                    data['Year'] = val
                    continue

                if tag == "TCON":
                    data['Genre'] = val
                    continue

                if tag == "TRCK":
                    data['Track'] = val
                    continue
            return data
        except IOError:
            pass


    ## Read tag based on initial information
    #  @return None if nothinig, else associative array.
    def read_tags(self):
        data = None
        if self.file_handle == None:
            return None

        if self.file_handle.closed:
            self.file_handle = open(self.filename, "r")

        if self.tag[0] == "id3v1":
            if self.tag[1] == "e":
                pass    # TODO:Need to find a test case
            else:
                data = self.id3v1()
        elif self.tag[0] == "id3v2":
            data = self.id3v2()
        
        self.file_handle.close()
        return data
