# This is an example of using 
# https://github.com/tensorflow/models/blob/master/research/object_detection/dataset_tools/create_pascal_tf_record.py
# The structure should be like PASCAL VOC format dataset
# +Dataset
#   +Annotations
#   +JPEGImages
# python create_tfrecords_from_xml.py --image_dir=dataset/JPEGImages 
#                                      --annotations_dir=dataset/Annotations 
#                                      --label_map_path=object-detection.pbtxt 
#                                      --output_path=data.record

import hashlib
import io
import logging
import os

from lxml import etree
import PIL.Image
import tensorflow as tf

from object_detection.utils import dataset_util
from object_detection.utils import label_map_util


flags = tf.app.flags
flags.DEFINE_string('image_dir', '', 'Path to image directory.')
flags.DEFINE_string('annotations_dir', '', 'Path to annotations directory.')
flags.DEFINE_string('output_path_train', '', 'Path to output TFRecord train')
flags.DEFINE_string('output_path_val', '', 'Path to output TFRecord val')
flags.DEFINE_string('label_map_path', 'data/pascal_label_map.pbtxt',
                    'Path to label map proto')
FLAGS = flags.FLAGS


def dict_to_tf_example(data, image_dir, label_map_dict):
    """Convert XML derived dict to tf.Example proto.

    Notice that this function normalizes the bounding
    box coordinates provided by the raw data.

    Arguments:
        data: dict holding XML fields for a single image (obtained by
          running dataset_util.recursive_parse_xml_to_dict)
        image_dir: Path to image directory.
        label_map_dict: A map from string label names to integers ids.

    Returns:
        example: The converted tf.Example.
    """
    full_path = os.path.join(image_dir, data['filename'])
    with tf.gfile.GFile(full_path, 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = PIL.Image.open(encoded_jpg_io)
    if image.format != 'JPEG':
        raise ValueError('Image format not JPEG')
    key = hashlib.sha256(encoded_jpg).hexdigest()

    width = int(data['size']['width'])
    height = int(data['size']['height'])

    xmin = []
    ymin = []
    xmax = []
    ymax = []
    classes = []
    classes_text = []

    print(data)

    try:
        print(data['filename'], 'objects: ')
        
        obj_cnt = 0

        for obj in data['object']:
            xmin.append(float(obj['bndbox']['xmin']) / width)
            ymin.append(float(obj['bndbox']['ymin']) / height)
            xmax.append(float(obj['bndbox']['xmax']) / width)
            ymax.append(float(obj['bndbox']['ymax']) / height)
            
            obj_name = obj['name'].strip()
            print('Object Name: ', obj_name)
            classes_text.append(obj_name.decode('utf8'))
            classes.append(label_map_dict[obj_name])
            obj_cnt += 1

        print('obj cnt:', obj_cnt, 'classes: ', classes_text)

    except KeyError as e:
        print(data['filename'] + ' without objects!')
        print(repr(e))

    difficult_obj = [0]*len(classes)
    example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(data['filename'].encode('utf8')),
        'image/source_id': dataset_util.bytes_feature(data['filename'].encode('utf8')),
        'image/key/sha256': dataset_util.bytes_feature(key.encode('utf8')),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature('jpeg'.encode('utf8')),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmin),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmax),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymin),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymax),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
        'image/object/difficult': dataset_util.int64_list_feature(difficult_obj)
    }))
    return example


def main(_):

    writer_train = tf.python_io.TFRecordWriter(FLAGS.output_path_train)
    writer_val = tf.python_io.TFRecordWriter(FLAGS.output_path_val)
    label_map_dict = label_map_util.get_label_map_dict(FLAGS.label_map_path)

    print('Label Map Dict:', label_map_dict)

    image_dir = FLAGS.image_dir
    annotations_dir = FLAGS.annotations_dir
    logging.info('Reading from dataset: ' + annotations_dir)
    examples_list = os.listdir(annotations_dir)

    #===
    num_examples = len(examples_list)
    num_train = int(0.8 * num_examples)
    #===

    #writer = writer_train

    for idx, example in enumerate(examples_list):
        if example.endswith('.xml'):

            #if idx == num_train:
            #    writer = writer_val
            #    print('Switching to val tfrecord')

            if idx % 10 == 0:
                print('On image %d of %d' % (idx, len(examples_list)))

            path = os.path.join(annotations_dir, example)
            with tf.gfile.GFile(path, 'r') as fid:
                xml_str = fid.read()
            xml = etree.fromstring(xml_str)
            data = dataset_util.recursive_parse_xml_to_dict(xml)['annotation']

            tf_example = dict_to_tf_example(data, image_dir, label_map_dict)
            
            if idx % 10 == 0:
                writer_val.write(tf_example.SerializeToString())
            else:
                writer_train.write(tf_example.SerializeToString())

    writer_train.close()    
    writer_val.close()
    



if __name__ == '__main__':
    tf.app.run()
    

# Import needed variables from tensorflow
# From tensorflow/models/research/
#protoc object_detection/protos/*.proto --python_out=.
#export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim
#python object_detection/builders/model_builder_test.py