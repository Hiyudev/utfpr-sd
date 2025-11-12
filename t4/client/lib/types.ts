export interface Leilao {
    name: string;
    description: string;
    value: number;
    start: Date;
    end: Date;
    id?: string;
}

export interface Message {
    event_name: string;
    [key: string]: any;
}