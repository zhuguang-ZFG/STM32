"""Regressions observed in multi-page narrated production."""
from pathlib import Path
import json,tempfile,unittest
import numpy as np
from PIL import Image,ImageDraw
import stroke_assets
from video_job import FilmBuilder,find_font
from smoke_test import write_test_tone

class ProductionRegressions(unittest.TestCase):
    def test_foreground_arm_is_not_owned_by_earlier_torso(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);font,index=find_font({});stroke_assets.configure_assets(root,font,index)
            image=Image.new('RGBA',(90,90));draw=ImageDraw.Draw(image)
            draw.rectangle((10,10,80,80),fill='#668CAE',outline='#202A35',width=3)
            draw.rectangle((25,30,70,48),fill='#E6B58F',outline='#202A35',width=3)
            source=root/'figure.png';image.save(source)
            whole=[[0,0],[1,0],[1,1],[0,1]];arm=[[.26,.32],[.8,.32],[.8,.56],[.26,.56]]
            meta=stroke_assets.build_illustration('parts',source,90,90,parts=[{'id':'torso','polygon':whole,'exclude_polygons':[arm]},{'id':'arm','polygon':arm}])
            maps=np.load(root/'parts.npz')
            self.assertEqual(maps['owners'][38,45],1)
            self.assertGreaterEqual(float(maps['color'][38,45])+1e-7,meta['parts'][1]['fill_start'])

    def test_short_caption_beat_can_share_longer_visual_group(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);Image.new('RGB',(640,360),'white').save(root/'cover.png')
            for name,seconds in [('long',3),('short',.72)]:write_test_tone(root/(name+'.wav'),seconds,220)
            manifest={'version':1,'runtime_fixture':True,'title':'跨句绘制','canvas':{'width':640,'height':360,'fps':24},'cover':{'source':'cover.png','seconds':1},'audio':{'trim_silence':False},'pages':[{'beats':[{'id':name,'text':'完整意思。' if name=='long' else '收束。','audio':name+'.wav'} for name in ('long','short')],'visual_groups':[{'start_beat':0,'end_beat':1,'lead':.2,'hold':.6,'actions':[{'type':'text','text':'跨句画面','x':30,'y':30,'size':36}]}]}]}
            (root/'job.json').write_text(json.dumps(manifest,ensure_ascii=False))
            timeline=FilmBuilder(root).build()
            self.assertEqual(len(timeline['pages'][0]['beats']),2)
            self.assertLess(timeline['pages'][0]['beats'][1]['duration'],1)
            self.assertGreater(timeline['pages'][0]['last_drawing_end'],timeline['pages'][0]['beats'][1]['start'])

    def test_pictures_draw_at_video_pace_and_then_hold(self):
        # A long window must not slow the pen down to fill it: unused time is handed back and the picture holds.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);Image.new('RGB',(640,360),'white').save(root/'cover.png')
            write_test_tone(root/'long.wav',9,220)
            image=Image.new('RGBA',(120,120));ImageDraw.Draw(image).rectangle((10,10,110,110),fill='#F1924A',outline='#252B39',width=4)
            image.save(root/'box.png')
            box={'type':'illustration','source':'box.png','x':300,'y':120,'width':120,'height':120,'parts':[{'id':'box','polygon':[[0,0],[1,0],[1,1],[0,1]]}]}
            manifest={'version':1,'runtime_fixture':True,'title':'画完停住','canvas':{'width':640,'height':360,'fps':24},'cover':{'source':'cover.png','seconds':1},
                      'audio':{'trim_silence':False},'pages':[{'beats':[{'id':'long','text':'一句很长的话。','audio':'long.wav',
                      'actions':[{'type':'text','text':'标题','x':30,'y':30,'size':40},box]}]}]}
            (root/'job.json').write_text(json.dumps(manifest,ensure_ascii=False))
            # A previous build numbered the picture first; its layers must not attach to whatever now has its name.
            (root/'work/assets').mkdir(parents=True);image.save(root/'work/assets/element-0001-line.png')
            timeline=FilmBuilder(root).build()
            self.assertFalse((root/'work/assets/element-0001-line.png').exists())
            self.assertNotEqual(timeline['assets']['element-0001']['type'],'illustration')
            page=timeline['pages'][0]
            drawings=[event for event in page['events'] if not event['caption']]
            for event in drawings:
                asset=timeline['assets'][event['asset']]
                seconds=asset['seconds'] if asset['type']=='illustration' else asset['handwriting']['seconds']
                self.assertAlmostEqual(event['end']-event['start'],seconds,places=6)
            self.assertGreater(page['speech_end']-page['last_drawing_end'],4)

if __name__=='__main__':unittest.main()
