import { ArrowUpRight, ChevronDown, Clock3, MapPin } from 'lucide-react';
import { formatMessage, localize, tr } from './i18n_多语言';
import type { CampusPlace, Lang } from './types_类型';

export default function CampusPlaceCard({ place, lang }: { place: CampusPlace; lang: Lang }) {
  const name = localize(place.name, lang);
  const address = formatMessage(tr(lang, '{building} {number}동 · {floor}층', '{building} {number} 号楼 · {floor} 楼'), {
    building: localize(place.building, lang),
    number: place.building_number,
    floor: place.floor,
  });
  return (
    <details className="place-card" data-testid={`place-${place.id}`}>
      <summary className="place-summary">
        <MapPin size={18} aria-hidden="true"/>
        <span>
          <strong>{name}</strong>
          <span>{address}</span>
        </span>
        <ChevronDown className="place-chevron" size={16} aria-hidden="true"/>
      </summary>
      <div className="place-content">
        <p>{localize(place.note, lang)}</p>
        <div className="place-hours-label"><Clock3 size={15} aria-hidden="true"/>{tr(lang, '운영 시간', '开放时间')} <span>KST</span></div>
        <dl className="place-hours">
          {place.hours.map(row => <div key={localize(row.label, 'ko')}>
            <dt>{localize(row.label, lang)}</dt><dd>{localize(row.time, lang)}</dd>
          </div>)}
        </dl>
        <div className="place-links">
          <a href={place.map_url} target="_blank" rel="noopener noreferrer">
            {tr(lang, '캠퍼스 지도 열기', '打开校园地图')}<ArrowUpRight size={14} aria-hidden="true"/>
          </a>
          {place.sources.map(source => <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">
            {localize(source.label, lang)}<ArrowUpRight size={14} aria-hidden="true"/>
          </a>)}
        </div>
      </div>
    </details>
  );
}
