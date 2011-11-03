import unittest
import json
from fixtures import demos

class TestBasicMedia(unittest.TestCase):
    
    def test_media_instance_to_json(self):
        
        obj_from_json = json.loads(demos.m.to_json())
        
        # More general check for ID
        self.assertEquals(
            36,
            len(obj_from_json.pop('_id')))
        
        self.assertEquals({
                        '_cls'  : 'Media',
                        '_types': ['Media'],
                        'title' : 'Misc Media'
                        }, obj_from_json)
                
        
    def test_media_class_to_jsonschema(self):
        self.assertEquals(
            json.dumps({
                    'title' : 'Media',
                    'type'  : 'object',
                    'properties': {
                        'owner' : {
                            'type' : 'string',
                            'title': 'owner'
                            },
                        'title' : {
                            'type' : 'string',
                            'title': 'title',
                            'maxLength': 40
                            }
                        }}),
            demos.Media.to_jsonschema()
            )

if __name__ == '__main__':
    unittest.main()

