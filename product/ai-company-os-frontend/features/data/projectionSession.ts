/** Never revive a result from a previous mounted reader, even for the same key. */
import type {ReadState} from './projectionRead';
export type SessionEntry<T>={owner:object;state:ReadState<T>};
export function sessionReadState<T>(owner:object,entry:SessionEntry<T>|null):ReadState<T>{
 return entry?.owner===owner?entry.state:{phase:'idle',data:null};
}
