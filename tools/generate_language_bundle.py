#!/usr/bin/env python

# Script for generating a language pack from an existing Pentaho installation.
#
# Existing translations are reused and any missing tokens are appended with "<TRANSLATE ME>"


import os
import sys
import shutil
import zipfile
import codecs

languageCode = sys.argv[1] # language as it is typed by the user
languageCode_underscore = languageCode.replace('-', '_').replace(' ', '_'); # this is the java way, valid for the .properties files
languageCode_hyphen = languageCode.replace('_', '-').replace(' ', '-');  # this seems to be the IETF standard, and what dojo and all .js are using
languageCode_slash = '/' + languageCode + '/';
jar_whitelist = ['pivot4j-analytics', 'pivot4j-core', 'pentaho-platform-'] # list of jars that will be scanned for messages.
#file_blacklist = ['system/common-ui/resources/messages']

origin_folder = os.path.abspath(sys.argv[2].replace('file://', ''))
destination_folder = os.path.abspath(sys.argv[3].replace('file://', ''))
plugin_folder =  os.path.realpath(os.path.join(os.getcwd(), '..', '..')) # There is a subtle difference between using os.dirname(__FILE__) and os.getcwd()

force = False
translation_marker = '<TRANSLATE ME>'# not used anymore

def rreplace(s, old, new, occurrence=1):
    # like str.replace, but starts from the end
    # by default, only the last occurrence is replaced
    li = s.rsplit(old, occurrence)
    return new.join(li)

def ensure_parent_folder_exists(dst):
    dst_parent = os.path.dirname(dst);
    if not os.path.exists(dst_parent):
        os.makedirs(dst_parent)
    return dst # allow for chaining

def copy(src, dst, patch=False, marker=translation_marker):
    ensure_parent_folder_exists(dst)

    # Copy files, optionally patching an existing file
    print '\nCopying: ' +  os.path.realpath(os.path.join(origin_folder, src)) + '\nto ' + dst
    if patch:
        with codecs.open(src, 'r', 'utf-8') as fin:
            lines_src = fin.readlines()

        add_missing_properties(lines_src, dst, encoding='utf-8', marker=marker)
    else:
        shutil.copy2(src, dst)
        convert_to_utf8(dst)


def add_missing_properties(lines_src, dst_localised, encoding='utf-8', marker=translation_marker):
    if os.path.exists(dst_localised):
        with codecs.open(dst_localised, 'a+', encoding, errors='ignore') as fout:
            fout.seek(0)
            lines_dst = fout.readlines()
            #print 'File ' + dst_localised + ' contains' , len(lines_dst), 'lines'
            for line in lines_src:
                keyval = line.split('=')
                if len(keyval) > 1:
                    found_line = False
                    for current_line_dst in lines_dst:
                        if (keyval[0].strip() in current_line_dst):
                            #print ' Ignoring existing key: ' + keyval[0].strip() + ' in file: ' + dst_localised
                            found_line = True
                            break

                    if not found_line:
                        print ' Adding missing key: ' + keyval[0].strip() + ' to file: ' + dst_localised
                        #fout.seek(0, 2)
                        fout.write(line.strip() + marker + '\n')

    else:
        print 'Patching: ' +  os.path.realpath(dst_localised)
        ensure_parent_folder_exists(dst_localised)
        with codecs.open(dst_localised, 'w', 'utf-8') as fout:
            for line in lines_src:
                keyval = line.split('=')
                if len(keyval) > 1:
                    #print ' Adding missing key: ' + keyval[0] + ' to file: ' + dst_localised
                    fout.write(line.strip() + translation_marker + '\n')
                else:
                    fout.write(line)


def convert_to_utf8(filename, backup=False):
    # gather the encodings you think that the file may be
    # encoded inside a tuple
    encodings = ('utf-8','iso-8859-1', 'ascii')

    # try to open the file and exit if some IOError occurs
    try:
        f = open(filename, 'r').read()
    except Exception:
        sys.exit(1)

    # now start iterating in our encodings tuple and try to
    # decode the file
    for enc in encodings:
        try:
            # try to decode the file with the first encoding
            # from the tuple.
            # if it succeeds then it will reach break, so we
            # will be out of the loop (something we want on
            # success).
            # the data variable will hold our decoded text
            data = f.decode(enc)
            break
        except Exception:
            # if the first encoding fail, then with the continue
            # keyword will start again with the second encoding
            # from the tuple an so on.... until it succeeds.
            # if for some reason it reaches the last encoding of
            # our tuple without success, then exit the program.
            if enc == encodings[-1]:
                sys.exit(1)
            continue

    if backup:
        # now get the absolute path of our filename and append .bak
        # to the end of it (for our backup file)
        fpath = os.path.abspath(filename)
        newfilename = fpath + '.bak'
        # and make our backup file with shutil
        shutil.copy(filename, newfilename)

    # and at last convert it to utf-8
    f = open(filename, 'w')
    try:
        f.write(data.encode('utf-8'))
    except Exception, e:
        print e
    finally:
        f.close()

def copy_and_edit_js(src_filename, dst_filename):
    # Copy template js and attempt to fix the languageCode, e.g. "en" -> "pt_PT"
    # copy(src_filename, dst_filename)
    ensure_parent_folder_exists(dst_filename)

    replacements = { 'dojo.provide(\"dojo.nls.dojo-analyzer_en\"': 'dojo.provide(\"dojo.nls.dojo-analyzer_' + languageCode_hyphen.lower() + '\"',
                     'dojo.provide(\"dojo.nls.dojo-ext_en\"': 'dojo.provide(\"dojo.nls.dojo-ext_' + languageCode_hyphen.lower() + '\"',
                     'dojo.provide(\"dojo.nls.dojo-reportviewer_en\"': 'dojo.provide(\"dojo.nls.dojo-reportviewer_' + languageCode_hyphen.lower() + '\"',
                     'dojo.provide(\"dojo.nls.dojo-pirs_en\"': 'dojo.provide(\"dojo.nls.dojo-pirs_' + languageCode_hyphen.lower() + '\"',
                     '.en\"': '.' + languageCode_underscore.lower() + '\"',
                     '.en=': '.' + languageCode_underscore.lower() + '=',
                     '_en=': '_' + languageCode_underscore.lower() + '=',
                     '_en\"': '_' + languageCode_underscore.lower() + '\"'
    }
    with open(dst_filename, 'w') as outfile:
        with open(src_filename) as infile:
            for line in infile:
                for src, target in replacements.items():
                    line = line.replace(src, target)
                outfile.write(line)
#end def

def create_index_supported_languages(dst):
    ensure_parent_folder_exists(dst)
    with codecs.open(dst, 'w', 'utf-8') as fout:
        fout.write('#Language Pack Installer: no need to edit this file\n')

os.chdir(origin_folder)

# First round: copy files that are already translated, even if only partially
for root, dirs, filenames in os.walk('.'):
    for f in filenames:
        src = os.path.join(root, f)
        g = f.lower()

        # Ignore all source files belonging to this plugin
        if plugin_folder in os.path.realpath(os.path.join(origin_folder, src)):
            #print "Skipping file", src, ", (belongs to the plugin folder: ", plugin_folder, ')'
            continue

        dst =  os.path.realpath(os.path.join(destination_folder, root, f ))
        # Prevent existing files at destination from being overwritten
        if os.path.exists(dst): #and not dst.endswith('.js'):
            print "Skipped copying file", dst, "in the first round because it already exists"
            continue

        # Grab *messages_LANG.properties and  *supported_languages.properties
        if g.endswith('supported_languages.properties'):
            create_index_supported_languages(dst)
        elif g.endswith('messages_'+ languageCode_underscore.lower()  +'.properties'):
            copy(src, dst)
        elif g.endswith('messages_'+ languageCode_hyphen.lower()  +'.properties'):
            dst_fixed =  os.path.realpath(os.path.join(destination_folder, root, f.replace(languageCode_hyphen, languageCode_underscore) ))
            copy(src, dst_fixed)

       # Handle existing translations in jars
        if g.endswith('.jar'):
            for whitelist_item in jar_whitelist:
                if whitelist_item.lower() in g:
                    z = zipfile.ZipFile(src)
                    for el in z.namelist():
                        e = el.lower()
                        dst = os.path.realpath(os.path.join(destination_folder, root, f.replace('.jar', '_jar'), el.replace(languageCode_hyphen, languageCode_underscore) ))
                        if e.endswith('messages_'+ languageCode_underscore.lower()  +'.properties') or e.endswith('messages_'+ languageCode_hyphen.lower()  +'.properties'):
                            print 'Copying/patching:\n  ' +  os.path.realpath(os.path.join(origin_folder, src, el)) + '\nto\n  ' + dst + '\n'
                            tmpfolder = os.tmpnam()
                            z.extract(el, tmpfolder)
                            tmpfile = os.path.join(tmpfolder, el)
                            os.system('native2ascii -reverse -encoding utf-8 {0} {0}'.format(tmpfile))
                            copy(tmpfile, dst, patch=os.path.exists(dst), marker='')
                            os.remove(tmpfile)
                        elif e.endswith('supported_languages.properties'):
                            # this seems to never happen
                            create_index_supported_languages(dst)

        # Copy all *nls/*LANG*.js
        gg = src.lower() # Notice that gg means the full path in lowercase
        dst =  os.path.realpath(os.path.join(destination_folder, root, f ))
        js_patterns = [ '/'+languageCode_hyphen+'/', '_'+languageCode_hyphen+'.' ];
        if ('nls' in gg) and gg.endswith('.js'):
            for p in js_patterns:
                if p.lower() in gg:
                    copy(src, dst)



# Second round: fill in the gaps, generate missing files
for root, dirs, filenames in os.walk('.'):
    for f in filenames:
        g = f.lower()
        src = os.path.join(root, f)

        # Ignore all files belonging to this plugin
        if plugin_folder in os.path.realpath(os.path.join(origin_folder, src)):
            continue

        # Patch messages_LANG.properties with missing tokens
        if g.endswith('messages.properties'):
            dst_localised =  os.path.realpath(os.path.join(destination_folder, root, f.replace('.properties', '_' + languageCode_underscore + '.properties') ))
            with codecs.open(src, 'r', 'utf-8') as fin:
                lines_src = fin.readlines()
            try:
                add_missing_properties(lines_src, dst_localised)
                # break
                #except UnicodeDecodeError as e:
                #print "Error adding key  to " + dst_localised + ", attempting latin1 encoding"
                #add_missing_properties(lines_src, dst_localised, 'latin1')
            except Exception as e:
                print "==== \n   Error adding key to ".upper() + dst_localised
                print e
                print "===="

        # Patch messages_LANG.properties missing in jars
        if g.endswith('.jar'):
            for whitelist_item in jar_whitelist:
                if whitelist_item.lower() in g:
                    z = zipfile.ZipFile(src)
                    for el in z.namelist():
                        e = el.lower()
                        if e.endswith('messages.properties'):
                            dst = os.path.realpath(os.path.join(destination_folder, root, f.replace('.jar', '_jar'), el.replace('.properties', '_' + languageCode_underscore + '.properties') ))
                            fin = z.open(el, 'r') # Zipfiles don't support "with" statement
                            lines_src = fin.readlines()
                            fin.close()
                            add_missing_properties(lines_src, dst)

        # Generate missing *nls/*LANG.js
        gg = src.lower() # Notice that g means the full path
        if gg.endswith('.js') and ('nls' in gg):
            src_lang_code = ''
            dst = ''
            for s in ['/en-gb/', '/en-us/', '/en/', '_en.', '-en.']: # let's use english as template
                if (s in gg):
                    src_lang_code = s
                    dst  = rreplace(src, s, s[0] + languageCode_hyphen.lower() + s[len(s)-1])
            if len(src_lang_code) > 0:
                dst_localised =  os.path.realpath(os.path.join(destination_folder, dst ))
                if not os.path.exists(dst_localised):
                    if '/' in src_lang_code:
                        copy(src, dst_localised)
                    else:
                        copy_and_edit_js(src, dst_localised)

# Third round: convert the encoding of all *.properties to utf8
for root, dirs, filenames in os.walk(destination_folder):
    for f in filenames:
        g = f.lower()
        src = os.path.join(destination_folder, root, f)
        if g.endswith('messages_'+ languageCode_underscore.lower()  +'.properties'):
            print 'Converting to utf8: ' + src
            #convert_to_utf8(src)
            os.system('native2ascii -reverse {0} {0}'.format(src))
            #os.system('native2ascii -reverse -encoding utf-8 {0} {0}'.format(src)) # don't specify the encoding
        #elif g.endswith('.js'):
        #    os.system('native2ascii -reverse -encoding utf-8 {0} {0}'.format(src))

# Fourth round: eliminate tmp and cache files
tmp_files = ['/tmp', '/plugin-cache']
for root, dirs, filenames in os.walk(destination_folder):
    for f in filenames:
        dst = os.path.join(destination_folder, root,f)
        print "remove ?: " + dst
        g = dst.lower()
        for tmp in tmp_files:
            if g.endswith(tmp):
                try:
                    print "Removing folder: " + dst
                    shutil.rmtree( dst )
                except e:
                    pass
