/** Static evidence guide; never a read result, timestamp or permission. */
import type {ReadbackKey} from './readbackCatalog';
const guide:Record<ReadbackKey,{scope:string;limit:string}>={
 mvp:{scope:'Sekiz motorun sentetik tanılama nedenleri',limit:'Canlı motor sağlığı, sağlayıcı çağrısı veya gerçek ajan yok.'},
 admission:{scope:'Tek örnek admission ve rezervasyon',limit:'Gerçek harcama, grant veya hesap bakiyesi yok.'},
 outbox:{scope:'Tek tarihsel Outbox gözlemi',limit:'Teslimat, tekrar deneme veya olay akışı kanıtı değil.'},
 'office-workbench':{scope:'Tek örnek çalışma alanı',limit:'Gerçek ajan, hareket veya canlı konum yok.'},
 'task-budget':{scope:'Örnek görev ve bütçe kaydı',limit:'Muhasebe kaydı, harcama izni veya gerçek maliyet yok.'},
 lifecycle:{scope:'Terminal örneğinin beş olaylık geçmişi',limit:'Başarılı iş teslimi veya bağımsız kabul değil.'},
 'lifecycle-prefix':{scope:'Örnek lifecycle prefix ve lease geçmişi',limit:'Lease güncelliği, model çağrısı ve Memory ACL yetkisi kanıtlanmaz.'}
};
export function readbackBoundary(key:unknown){
 if(typeof key!=='string'||!Object.hasOwn(guide,key))return null;
 const {scope,limit}=guide[key as ReadbackKey];return {scope,limit,decision:'HOLD' as const};
}
