#!/usr/bin/env python3

from PIL import Image
import os
import sys
import shutil
import random

from multiprocessing import Pool, cpu_count
from tqdm import tqdm

# Global variables

## How many augmented images to create
AUGMENTED = 100
## Add unmodified images to the result
ADD_ORIGINAL = True
## Resample algorithm
RESAMPLE = Image.BICUBIC
## Degree of parallelism
THREAD_COUNT = cpu_count()

def random_rot(img):
    '''Rotate image by a random angle

    @param img: Image to rotate

    @return: Rotated image
    '''
    a = random.uniform(-15, 15)

    w, h = img.size

    # Try to rotate approximatelly around center
    cx = w * 0.5 + (random.random() - 0.5) / 2
    cy = h * 0.5 + (random.random() - 0.5) / 2
    
    return img.rotate(a, RESAMPLE, center = (cx, cy))

def random_crop(img):
    r = lambda : random.random() / 10.
    crob_box = (img.size[0] * r(), img.size[1] * r(),
                img.size[0] * (1 - r()), img.size[1] * (1 - r()))
    return img.crop(crob_box)
    

def modify(img):
    '''
    Adds some random modifications to the image and returns it

    @param img: Image to modify

    @return: Modified image
    '''
    orig_size = img.size


    res = random_crop(img)
    res = res.resize(orig_size, RESAMPLE)

    return res


def process_image(path_in, path_out):
    '''Modify an image and save it in another place

    @param path_in: Source path of the image

    @param path_out: Destination of the modified image
    '''
    im_in = Image.open(path_in)

    im_out = modify(im_in)

    im_out.save(path_out, "JPEG")


def copy_files(dir_in, dir_out):
    '''
    Copy unmodified images from original directory into a new one

    @param dir_in: Directory with source images

    @param dir_out: Directory where to store image
    '''
    images = os.listdir(dir_in)

    for image in images:
        path_in = os.path.join(dir_in, image)
        shutil.copy2(path_in, dir_out)
    

def process_category(dir_in, dir_out):
    '''Looks at the images in the directory and creates new randomized
    images
    '''

    if ADD_ORIGINAL:
        copy_files(dir_in, dir_out)
    
    images = os.listdir(dir_in)

    if len(images) == 0:
        print('[WARNING] Empty category: {}'.format(dir_in))
        return
        
    for i, orig in enumerate(random.choices(images, k = AUGMENTED)):
        path_in = os.path.join(dir_in, orig)
        path_out = os.path.join(dir_out, 'aug_{}_{}'.format(i, orig))
        process_image(path_in, path_out)


def _process_category(args):
    '''Wrapper around process_category to be passed to imap'''
    dir_in, dir_out, entry = args
    category_path = os.path.join(dir_in, entry)

    if not os.path.isdir(category_path):
        print("[WARNING] Unexpected entry: {}".format(entry))

    category_path_out = os.path.join(dir_out, entry)
    os.makedirs(category_path_out)

    process_category(category_path, category_path_out)


def process(dir_in, dir_out):
    if len(os.listdir(dir_out)) != 0:
        print("Expected empty out directory")
        print_usage()

    # Directories of categories
    directories = os.listdir(dir_in)
    total = len(directories)

    def generate_args():
        for entry in directories:
            yield dir_in, dir_out, entry

    with Pool(THREAD_COUNT) as pool:
        for _ in tqdm(pool.imap_unordered(_process_category, generate_args()), total=total):
            pass

    
def print_usage():
    print("Expected image directory")
    print("Usage: {} <in_dir> <out_dir>".format(sys.argv[0]))
    sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print_usage()
        
    dir_in = sys.argv[1]

    if not os.path.isdir(dir_in):
        print_usage()

    dir_out = sys.argv[2]

    if not os.path.exists(dir_out):
        print('[WARNING] Creating an output directory')
        os.makedirs(dir_out)
        
    if not os.path.isdir(dir_out):
        print_usage()

    process(dir_in, dir_out)

if __name__ == '__main__':
    main()
