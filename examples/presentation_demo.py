from pathlib import Path
import json,shutil,tempfile
from draftseam import DraftBundle,parse_bundle,write_bundle,insert_subtitle
from draftseam.writer import draft_to_dict
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="draftseam-demo-",dir=root/"examples") as directory:
 target=Path(directory)/"sample_project"
 shutil.copytree(root/"tests/fixtures/sample_project",target)
 bundle=DraftBundle(target);draft=parse_bundle(bundle)
 before={"tracks":len(draft.tracks),"texts":len(draft.materials.texts)}
 original_info=bundle.draft_info_path.read_bytes()
 original_model=draft_to_dict(draft)
 write_bundle(draft,bundle)
 roundtrip_equal=draft_to_dict(parse_bundle(bundle))==original_model
 insert_subtitle(draft,text="A new local subtitle",start=2.0,dur=1.5,material_id="presentation-subtitle")
 write_bundle(draft,bundle);after=parse_bundle(bundle)
 print(json.dumps({"before":before,"after":{"tracks":len(after.tracks),"texts":len(after.materials.texts)},"subtitle":after.materials.texts[-1].text,"roundtrip_equal":roundtrip_equal,"draft_info_unchanged":bundle.draft_info_path.read_bytes()==original_info},indent=2))
