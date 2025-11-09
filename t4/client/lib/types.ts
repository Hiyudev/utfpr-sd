export interface Leilao {
    name: string;
    description: string;
    value: number;
    start_date: Date;
    end_date: Date;
    id?: string;
}

export interface Message {
    event_name: string;
    [key: string]: any;
}